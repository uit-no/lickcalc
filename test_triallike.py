import csv
from trompy import lickcalc

# Load trial_like data
trial_like_onsets = []
with open('assets/examples/synthetic_edge_cases/synthetic_analysis_cases.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        onset_str = row['onset_trial_like'].strip()
        if onset_str:
            trial_like_onsets.append(float(onset_str))

print(f'Trial-like onsets ({len(trial_like_onsets)} licks):')
print(trial_like_onsets[:12])

# Test lickcalc with default IBI threshold
lickdata = lickcalc(trial_like_onsets, burstThreshold=0.25, minburstlength=2)
print(f'\nBurst analysis (IBI=0.25s):')
print(f'  Number of bursts: {lickdata["bNum"]}')
print(f'  Mean licks/burst: {lickdata["bMean"]}')
print(f'  burstprob is None: {lickdata["burstprob"] is None}')
if lickdata["burstprob"] is not None:
    print(f'  burstprob[0] length: {len(lickdata["burstprob"][0])}')
    print(f'  burstprob type: {type(lickdata["burstprob"])}')
    print(f'  burstprob data: {lickdata["burstprob"]}')
else:
    print('  burstprob is NONE!')
