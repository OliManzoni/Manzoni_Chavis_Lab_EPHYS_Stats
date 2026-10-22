"""Numerical analyses separated from UI; measurement definitions preserved."""
import tempfile
from pathlib import Path
import numpy as np
import pyabf
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d
from scipy import signal, integrate, ndimage


def read_abf(payload):
    with tempfile.NamedTemporaryFile(suffix='.abf', delete=False) as f:
        path = Path(f.name)
        f.write(payload)
    try:
        abf = pyabf.ABF(str(path))
        abf.setSweep(0)
        return abf
    finally:
        path.unlink(missing_ok=True)


def analyze_spikes(abf, spike_threshold, dvdt_threshold):
    abf.setSweep(0)
    if abf.sweepUnitsY != 'mV' or abf.sweepUnitsC not in ('pA','nA'):
        raise ValueError('L’analyse d’excitabilité attend une tension en mV et une commande en pA ou nA.')
    if abf.sweepLengthSec < 0.6:
        raise ValueError('Le protocole actuel attend des sweeps couvrant 100–600 ms.')
    unit_i, unit_v = abf.sweepUnitsC, abf.sweepUnitsY
    sr = abf.dataRate
    dt_ms = (1.0 / sr) * 1000.0  
    idx_start, idx_end = int(sr * 0.1), int(sr * 0.6) 

    courants, v_stat, v_peak, v_rest_list, n_spikes = [], [], [], [], []
    v_thresh_list, ap_amps, ap_widths, ap_rise, ap_decay, ap_ahp = [], [], [], [], [], []
    sweep_all_ahps_indices = [] 

    # Listes de suivi pour le bloc de dépolarisation
    excluded_sweeps = []
    is_excluded_list = []
    has_reached_rheobase = False

    for sweep in abf.sweepList:
        abf.setSweep(sweep)
        i_cmd = np.mean(abf.sweepC[idx_start:idx_end])
        v_r = np.mean(abf.sweepY[0:idx_start])
        v_s = np.mean(abf.sweepY[idx_end - int(sr*0.05) : idx_end])
        v_p = np.min(abf.sweepY[idx_start:idx_end]) if i_cmd < 0 else np.max(abf.sweepY[idx_start:idx_end])

        trace_win = abf.sweepY[idx_start:idx_end]

        min_dist_samples = int(sr * 0.003) 
        peaks, _ = find_peaks(trace_win, height=spike_threshold, distance=min_dist_samples)
        num_spikes = len(peaks)

        # --- DÉTECTION INTELLIGENTE DU DEPOLARIZATION BLOCK ---
        is_depol_block = False

        if num_spikes > 0:
            has_reached_rheobase = True # La cellule a prouvé qu'elle pouvait décharger
            if i_cmd > 0 and v_s > -45:
                # Arrêt précoce : On demande num_spikes > 1 pour ne pas faussement exclure la rhéobase
                if num_spikes > 1 and peaks[-1] < int((idx_end - idx_start) * 0.6):
                    is_depol_block = True
        else:
            # 0 Spike : Est-ce un Depol Block ou juste avant la rhéobase ?
            if i_cmd > 0 and v_s > -45:
                # Ne déclenche le bloc que si on a déjà dépassé la rhéobase lors d'un sweep précédent
                if has_reached_rheobase:
                    is_depol_block = True

        if is_depol_block:
            excluded_sweeps.append(sweep)
        is_excluded_list.append(is_depol_block)

        vt, amp, width, rise, decay, ahp_1st = [np.nan]*6
        ahp_indices_for_current_sweep = []

        if num_spikes > 0:
            pk_idx_1st = peaks[0]
            s_start = max(0, pk_idx_1st - int(sr * 0.015))
            seg = trace_win[s_start:pk_idx_1st]

            if len(seg) > 1:
                smoothed = gaussian_filter1d(seg, sigma=1)
                dvdt = np.diff(smoothed) / dt_ms
                cross = np.where(dvdt > dvdt_threshold)[0]

                if len(cross) > 0:
                    idx_t_seg = cross[0]
                    vt = seg[idx_t_seg]
                    idx_t_glob = s_start + idx_t_seg
                    amp = trace_win[pk_idx_1st] - vt

                    if amp > 0:
                        v50 = vt + 0.5*amp; v10 = vt + 0.1*amp; v90 = vt + 0.9*amp
                        up = trace_win[idx_t_glob:pk_idx_1st]

                        dn_end_1st = peaks[1] if num_spikes > 1 else min(len(trace_win), pk_idx_1st + int(sr * 0.1))
                        dn_1st = trace_win[pk_idx_1st:dn_end_1st]

                        r10 = np.where(up >= v10)[0]; r90 = np.where(up >= v90)[0]
                        if len(r10)>0 and len(r90)>0: rise = (r90[0]-r10[0])*dt_ms

                        d90 = np.where(dn_1st <= v90)[0]; d10 = np.where(dn_1st <= v10)[0]
                        if len(d90)>0 and len(d10)>0: decay = (d10[0]-d90[0])*dt_ms

                        wup = np.where(up >= v50)[0]; wdn = np.where(dn_1st <= v50)[0]
                        if len(wup)>0 and len(wdn)>0: width = ((pk_idx_1st+wdn[0])-(idx_t_glob+wup[0]))*dt_ms

            for i, pk_idx in enumerate(peaks):
                max_search_window = pk_idx + int(sr * 0.05) 

                if i < num_spikes - 1:
                    ahp_end = min(max_search_window, peaks[i+1])
                else:
                    ahp_end = min(max_search_window, len(trace_win))

                dn_segment = trace_win[pk_idx:ahp_end]

                if len(dn_segment) > 0:
                    local_min_idx = np.argmin(dn_segment)
                    global_ahp_idx = idx_start + pk_idx + local_min_idx
                    ahp_indices_for_current_sweep.append(global_ahp_idx)

                    if i == 0:
                        ahp_1st = dn_segment[local_min_idx]

        courants.append(i_cmd); v_stat.append(v_s); v_peak.append(v_p)
        v_rest_list.append(v_r); n_spikes.append(num_spikes); v_thresh_list.append(vt)
        ap_amps.append(amp); ap_widths.append(width); ap_rise.append(rise); ap_decay.append(decay); ap_ahp.append(ahp_1st)
        sweep_all_ahps_indices.append(ahp_indices_for_current_sweep)

    # --- CALCULS GLOBAUX ÉCHANTILLONNÉS (SANS LES TRACES EXCLUES) ---
    valid_indices = [i for i, excl in enumerate(is_excluded_list) if not excl]

    v_rest_final = np.mean(v_rest_list)
    neg = [i for i, c in enumerate(courants) if c < 0]
    rin, tau = np.nan, np.nan
    if neg:
        neg_s = sorted(neg, key=lambda i: abs(courants[i]))[:4]
        rin = np.polyfit([courants[i] for i in neg_s]+[0], [v_stat[i] for i in neg_s]+[v_rest_final], 1)[0] * (1 if unit_i=="nA" else 1000)
        idx_t = sorted(neg, key=lambda i: abs(courants[i]))[0]
        abf.setSweep(idx_t)
        v_targ = np.mean(abf.sweepY[idx_start-int(sr*0.01):idx_start]) + 0.632*(v_stat[idx_t]-np.mean(abf.sweepY[idx_start-int(sr*0.01):idx_start]))
        cross_t = np.where(abf.sweepY[idx_start:idx_end] <= v_targ)[0]
        if len(cross_t)>0: 
            tau = (cross_t[0]/sr)*1000.0

    # Recherche de la Rhéobase uniquement parmi les sweeps valides
    rheo_idx_global = next((i for i in valid_indices if n_spikes[i] > 0), None)
    rheo_v = v_thresh_list[rheo_idx_global] if rheo_idx_global is not None else np.nan
    rheo_i = courants[rheo_idx_global] if rheo_idx_global is not None else np.nan

    return {'unit_i': unit_i, 'unit_v': unit_v, 'sr': sr, 'dt_ms': dt_ms, 'idx_start': idx_start, 'idx_end': idx_end, 'courants': courants, 'v_stat': v_stat, 'v_peak': v_peak, 'v_rest_list': v_rest_list, 'n_spikes': n_spikes, 'v_thresh_list': v_thresh_list, 'ap_amps': ap_amps, 'ap_widths': ap_widths, 'ap_rise': ap_rise, 'ap_decay': ap_decay, 'ap_ahp': ap_ahp, 'sweep_all_ahps_indices': sweep_all_ahps_indices, 'excluded_sweeps': excluded_sweeps, 'is_excluded_list': is_excluded_list, 'valid_indices': valid_indices, 'v_rest_final': v_rest_final, 'rin': rin, 'tau': tau, 'rheo_idx_global': rheo_idx_global, 'rheo_v': rheo_v, 'rheo_i': rheo_i}


def calculate_rise_time_expert(segment_y, dt):
    segment_y = np.asarray(segment_y, dtype=float)
    if segment_y.size < 4 or not np.all(np.isfinite(segment_y)):
        return np.nan
    peak_idx = int(np.argmax(segment_y))
    peak = float(segment_y[peak_idx])
    if peak_idx < 2 or peak <= 0:
        return np.nan
    rising = segment_y[: peak_idx + 1]
    crossings = []
    for fraction in (0.10, 0.90):
        level = fraction * peak
        above = np.flatnonzero(rising >= level)
        if not above.size:
            return np.nan
        idx = int(above[0])
        if idx == 0 or rising[idx] == rising[idx - 1]:
            crossings.append(idx * dt)
        else:
            crossings.append(((idx - 1) + (level - rising[idx - 1]) / (rising[idx] - rising[idx - 1])) * dt)
    return max(0.0, crossings[1] - crossings[0])


def analyze_ipsc(abf, dynamic, use_bessel, cutoff, is_outward, threshold,
                 use_amp_filter, amp_limit, use_decay_filter, decay_limit,
                 use_rise_filter, rise_limit):
    abf.setSweep(0)
    fs, times, dt = abf.dataRate, abf.sweepX, 1000/abf.dataRate
    applied_cutoff = min(cutoff, max(1, int(.95*fs/2)))
    # Ligne de base
    if dynamic:
        raw_data = ndimage.median_filter(abf.sweepY, size=int(0.5 * fs))
        raw_data = abf.sweepY - raw_data
    else:
        raw_data = abf.sweepY - np.median(abf.sweepY)

    # Filtrage
    f_data = raw_data
    if use_bessel:
        nyq = 0.5 * fs
        b, a = signal.bessel(4, applied_cutoff/nyq, btype='low', analog=False)
        f_data = signal.filtfilt(b, a, raw_data)

    # Détection
    detect_trace = f_data if is_outward else -f_data

    best_corr = np.zeros_like(detect_trace)
    decays = [10.0, 20.0, 30.0, 50.0] if is_outward else [2.0, 5.0, 10.0, 15.0]

    for d in decays:
        t_tmpl = np.arange(0, 30, dt)
        tmpl = (np.exp(-t_tmpl/d) - np.exp(-t_tmpl/0.5)) 
        tmpl /= np.max(np.abs(tmpl))
        best_corr = np.maximum(best_corr, signal.correlate(detect_trace, tmpl, mode='same'))

    corr_scale = np.std(best_corr)
    if not np.isfinite(corr_scale) or corr_scale == 0:
        raise ValueError("Le signal ne présente pas de variation détectable après prétraitement.")
    corr_z = (best_corr - np.mean(best_corr)) / corr_scale
    peaks, _ = signal.find_peaks(corr_z, height=threshold, distance=int(0.005 * fs))

    valid_ev = []
    k_trace = f_data

    for i, p in enumerate(peaks):
        start, end = p - int(0.005*fs), p + int(0.030*fs)
        if start < 0 or end >= len(k_trace): continue

        l_base = np.mean(k_trace[p-int(0.005*fs):p-int(0.002*fs)])

        if is_outward:
            seg = k_trace[start:end] - l_base
        else:
            seg = -(k_trace[start:end] - l_base)

        amp = np.max(seg)
        rise_1090 = calculate_rise_time_expert(seg, dt)
        area = integrate.trapezoid(seg, dx=dt)

        estimated_decay = abs(area / amp) if amp > 0 else 0

        # Utilisation de la nouvelle limite absolue
        pass_amp = (not use_amp_filter or amp >= amp_limit)
        pass_decay = (not use_decay_filter or estimated_decay <= decay_limit)
        pass_rise = (not use_rise_filter or rise_1090 <= rise_limit)

        if pass_amp and pass_decay and pass_rise:
            ev = {'idx': p, 'time': times[p], 'amp': amp, 'rise': rise_1090, 'area': abs(area), 'decay': estimated_decay}
            ev['iei'] = (times[p] - valid_ev[-1]['time'])*1000 if valid_ev else np.nan
            valid_ev.append(ev)

    return dict(fs=fs, times=times, dt=dt, f_data=f_data, corr_z=corr_z, valid_ev=valid_ev, applied_cutoff=applied_cutoff)


def robust_z_score(sig):
    med = np.median(sig)
    mad = np.median(np.abs(sig - med))
    if mad == 0: return (sig - np.mean(sig)) / (np.std(sig) + 1e-9)
    return (sig - med) / (1.4826 * mad)

def get_true_peaks(corr_peaks, detect_trace, search_window, fs):
    if len(corr_peaks) == 0: return []
    true_peaks = []
    for cp in corr_peaks:
        start_search = max(0, cp - search_window)
        end_search = min(len(detect_trace), cp + search_window)
        local_max_idx = start_search + np.argmax(detect_trace[start_search:end_search])
        true_peaks.append(local_max_idx)
    true_peaks = sorted(list(set(true_peaks)))
    filtered_peaks = [true_peaks[0]]
    for p in true_peaks[1:]:
        if p - filtered_peaks[-1] > int(0.002 * fs):
            filtered_peaks.append(p)
    return filtered_peaks

def calculate_epsc_rise_time(segment_y, dt):
    """Return the first 10–90% threshold-crossing interval in milliseconds."""
    segment_y = np.asarray(segment_y, dtype=float)
    if segment_y.size < 4 or not np.all(np.isfinite(segment_y)):
        return np.nan
    peak_idx = int(np.argmax(segment_y))
    peak = float(segment_y[peak_idx])
    if peak_idx < 2 or peak <= 0:
        return np.nan

    rising = segment_y[: peak_idx + 1]
    crossings = []
    for fraction in (0.10, 0.90):
        threshold_value = fraction * peak
        above = np.flatnonzero(rising >= threshold_value)
        if not above.size:
            return np.nan
        idx = int(above[0])
        if idx == 0:
            crossings.append(0.0)
        else:
            y0, y1 = rising[idx - 1], rising[idx]
            if y1 == y0:
                crossings.append(idx * dt)
            else:
                crossings.append(((idx - 1) + (threshold_value - y0) / (y1 - y0)) * dt)
    return max(0.0, crossings[1] - crossings[0])

def analyze_epsc(abf, dynamic, use_bessel, cutoff, threshold, use_amp_filter, amp_limit, use_rise_filter, rise_limit):
    abf.setSweep(0)
    fs, times, dt = abf.dataRate, abf.sweepX, 1000/abf.dataRate

    if dynamic:
        raw_data = ndimage.median_filter(abf.sweepY, size=int(0.5 * fs))
        raw_data = abf.sweepY - raw_data
    else:
        raw_data = abf.sweepY - np.median(abf.sweepY)

    f_data = raw_data
    if use_bessel:
        nyq = 0.5 * fs
        b, a = signal.bessel(4, cutoff/nyq, btype='low', analog=False)
        f_data = signal.filtfilt(b, a, raw_data)

    detect_trace = -f_data 
    best_corr_base = np.zeros_like(detect_trace)
    for d in [2.0, 5.0, 10.0, 15.0]:
        t_tmpl = np.arange(0, 20, dt)
        tmpl = (np.exp(-t_tmpl/d) - np.exp(-t_tmpl/0.5)) 
        tmpl /= np.max(np.abs(tmpl))
        best_corr_base = np.maximum(best_corr_base, signal.correlate(detect_trace, tmpl, mode='same'))

    corr_z_base = robust_z_score(best_corr_base)
    peaks_base_corr, _ = signal.find_peaks(corr_z_base, height=threshold, distance=int(0.005 * fs))
    peaks_base = get_true_peaks(peaks_base_corr, detect_trace, search_window=int(0.010 * fs), fs=fs)

    valid_ev_base = []
    window_pre = int(0.005 * fs)
    window_post = int(0.025 * fs)
    extracted_waveforms = []

    for i, p in enumerate(peaks_base):
        start, end = p - window_pre, p + window_post
        if start < 0 or end >= len(f_data): continue

        l_base = np.mean(f_data[p-window_pre:p-int(0.002*fs)])
        seg = -(f_data[start:end] - l_base)
        amp = seg[window_pre] 
        rise_1090 = calculate_epsc_rise_time(seg, dt)

        if (not use_amp_filter or amp >= amp_limit) and (not use_rise_filter or rise_1090 <= rise_limit):
            ev = {'idx': p, 'time': times[p], 'amp_peak': amp, 'rise': rise_1090}
            ev['iei'] = (times[p] - valid_ev_base[-1]['time'])*1000 if valid_ev_base else np.nan
            valid_ev_base.append(ev)
            extracted_waveforms.append(seg)

    # --- PASSE 2 ---
    valid_ev_iter = []
    avg_waveform = np.array([])
    has_waveforms = len(extracted_waveforms) > 5

    if has_waveforms:
        avg_waveform = np.median(extracted_waveforms, axis=0)
        avg_waveform -= np.mean(avg_waveform[:int(0.002*fs)])
        avg_waveform = np.clip(avg_waveform, 0, None)
        if np.max(avg_waveform) > 0: avg_waveform /= np.max(avg_waveform) 

        template_area = integrate.trapezoid(avg_waveform, dx=dt)
        corr_iter = signal.correlate(detect_trace, avg_waveform, mode='same')
        corr_z_iter = robust_z_score(corr_iter)

        peaks_iter_corr, _ = signal.find_peaks(corr_z_iter, height=threshold, distance=int(0.005 * fs))
        peaks_iter = get_true_peaks(peaks_iter_corr, detect_trace, search_window=int(0.010 * fs), fs=fs)

        for i, p in enumerate(peaks_iter):
            start, end = p - window_pre, p + window_post
            if start < 0 or end >= len(f_data): continue

            l_base = np.mean(f_data[p-window_pre:p-int(0.002*fs)])
            seg = -(f_data[start:end] - l_base)
            scale_factor = np.dot(seg, avg_waveform) / (np.dot(avg_waveform, avg_waveform) + 1e-9)

            if (not use_amp_filter or scale_factor >= (amp_limit * 0.75)): 
                ev = {'idx': p, 'time': times[p], 'amp_scaled': scale_factor, 
                      'charge_scaled': scale_factor * template_area, 
                      'rise': calculate_epsc_rise_time(seg, dt)}
                ev['iei'] = (times[p] - valid_ev_iter[-1]['time'])*1000 if valid_ev_iter else np.nan
                valid_ev_iter.append(ev)

    return dict(has_waveforms=has_waveforms, times=times, f_data=f_data,
                corr_z_iter=corr_z_iter if has_waveforms else None,
                valid_ev_iter=valid_ev_iter, valid_ev_base=valid_ev_base,
                avg_waveform=avg_waveform, dt=dt, fs=fs)
