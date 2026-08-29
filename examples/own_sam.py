from cge_core import StandardCGE

# Canonical Hosoe-labelled SAM:
economy = StandardCGE.from_sam("sam.csv")
base = economy.solve()
print(base.summary().to_string(index=False))
