import matplotlib.pyplot as plt

thresholds_up = []
hits_up = []
thresholds_dn = []
hits_dn = []
dn = True
with open("test_tune2.log") as f:
    while True:
        threshold_line = f.readline()
        if threshold_line == '':
            break
        threshold_parts = threshold_line.split(": ")
        threshold = threshold_parts[-1][:-1]
        if threshold == "70":
            dn = False
        hit_line = f.readline()
        hit_parts = hit_line.split(":")
        hit = hit_parts[-1][:-1]
        if dn:
            thresholds_dn.append(threshold)
            hits_dn.append(hit)
        else:
            thresholds_up.append(threshold)
            hits_up.append(hit)

map(int, thresholds_dn)
map(int, hits_dn)
map(int, thresholds_up)
map(int, hits_up)
print thresholds_dn
print thresholds_up
plt.plot(thresholds_dn, hits_dn, 'r')
plt.plot(thresholds_up, hits_up, 'b')
plt.show()
