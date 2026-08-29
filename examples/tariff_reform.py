from cge_core import StandardCGE

base = StandardCGE.example().solve()
reform = base.scenario("Tariff abolition")
reform.tariff("BRD", 0)
result = reform.solve()

print(result.summary().to_string(index=False))
print(result.compare(base).to_string(index=False))
