from cge_core import CamCGE

base = CamCGE.example().solve()
print(base.summary().to_string(index=False))
print("Published CAMCGE objective reference: 191.7346")
