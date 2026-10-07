"""Explain recorded rule evidence without changing the upstream verdict."""
from .engine import Config
from bisect import bisect_left, bisect_right


def enrich_reps(reps: list[dict], samples: list[dict], mode: str) -> None:
    config = Config(mode=mode)
    timestamps = [s['t'] for s in samples]
    for rep in reps:
        window = [s for s in samples[bisect_left(timestamps, rep['start_s']):bisect_right(timestamps, rep['end_s'])] if s['validity'] == 'valid']
        details = []
        for code in rep['fault_codes']:
            if code == 'shallow':
                details.append(dict(code=code, label='Accepted bottom phase was not recorded',
                    explanation=f"Maximum thigh inclination was {rep['max_thigh_angle']}°. The {mode} bottom band is {config.pass_start}–95°. The recorded state sequence returned to standing without an accepted bottom phase. This can mean insufficient inclination or that tracking/sampling missed the configured band; the peak alone does not distinguish them.",
                    suggestion='Review the angle trace through the configured bottom range. Keep the full body side-on and the movement controlled.',
                    time_s=rep['bottom_s'], measured=rep['max_thigh_angle'], threshold=config.pass_start, affects_verdict=True))
            elif code in ('shin_over_toe', 'too_deep'):
                field, threshold = ('shin_angle', config.ankle_limit) if code == 'shin_over_toe' else ('thigh_angle', 95)
                candidates = [s for s in window if s.get(field) is not None and s[field] > threshold]
                peak = max(candidates, key=lambda s:s[field]) if candidates else None
                details.append(dict(code=code,
                    label='Forward shin inclination exceeded the rule' if code == 'shin_over_toe' else 'Thigh inclination exceeded the rule',
                    explanation=f"The configured limit is {threshold}°." + (f" The recorded peak was {peak[field]}°." if peak else ' The failing cue was latched before this repetition boundary; its trigger measurement is outside this recorded interval.') + (' This angle heuristic does not measure whether the knee crosses the toes in 3D.' if code == 'shin_over_toe' else ' This is an image angle, not a medical limit on squat depth.'),
                    suggestion='Review this moment side-by-side with the video. Reduce the measured forward shin tilt.' if code == 'shin_over_toe' else 'Review the bottom position and use the configured angle range if comfortable.',
                    time_s=peak['t'] if peak else rep['bottom_s'], measured=peak[field] if peak else None,
                    threshold=threshold, affects_verdict=True))
        for code, field, threshold, direction in [('bend_backward','hip_angle',50,'above'),('bend_forward','hip_angle',config.hip_min,'below')]:
            shown = [s for s in window if code in s.get('feedback_codes',[]) and s.get(field) is not None and (s[field] > threshold if direction == 'above' else s[field] < threshold)]
            if shown:
                peak = (max if direction == 'above' else min)(shown,key=lambda s:s[field])
                details.append(dict(code=code,label='Torso-position cue',
                    explanation=f"The upstream hip-to-vertical proxy reached {peak[field]}°, {direction} its {threshold}° cue threshold. This advisory does not itself make the repetition improper.",
                    suggestion='Replay the cue and review torso position; interpret it together with the camera view.',
                    time_s=peak['t'], measured=peak[field],threshold=threshold,affects_verdict=False))
        rep['feedback_details'] = details
        rep['review_summary'] = 'No failing upstream rule was triggered in this completed repetition.' if rep['verdict'] == 'correct' else 'The recorded repetition triggered the failing rule(s) listed below.'
