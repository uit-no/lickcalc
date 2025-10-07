from trompy import lickcalc

# Test if remove_longlicks works with onset-only data
onset_times = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]

print("Testing remove_longlicks parameter...")

# Test with onset only
result1 = lickcalc(onset_times, remove_longlicks=False)
result2 = lickcalc(onset_times, remove_longlicks=True)

print(f"Onset only - False: {result1['total']} licks")
print(f"Onset only - True: {result2['total']} licks")

if result1['total'] == result2['total']:
    print("❗ remove_longlicks has NO EFFECT with onset-only data!")
    print("   This parameter likely requires offset data to work.")
else:
    print("✅ remove_longlicks works with onset-only data")

# Test with onset + offset data
offset_times = [0.1, 0.6, 1.1, 1.6, 2.4, 2.8, 3.2]  # Some are long licks

result3 = lickcalc(onset_times, offset=offset_times, longlickThreshold=0.3, remove_longlicks=False)
result4 = lickcalc(onset_times, offset=offset_times, longlickThreshold=0.3, remove_longlicks=True)

print(f"With offset - False: {result3['total']} licks")
print(f"With offset - True: {result4['total']} licks")

if result3['total'] != result4['total']:
    print("✅ remove_longlicks WORKS with offset data!")
else:
    print("❗ remove_longlicks still has no effect even with offset data")