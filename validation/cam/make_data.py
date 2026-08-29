"""Emit camcge base data (GAMS lib SEQ=81 / WB DRD290) as CGE-Core CSVs."""
import csv
from pathlib import Path
I = ["ag-subsist","ag-exp+ind","sylvicult","ind-alim","biens-cons",
     "biens-int","cim-int","biens-cap","construct","services","publiques"]
LC = ["rural","urban-unsk","urban-skil"]
io = {  # io[row][col] - input-output coefficients, blanks = 0
"ag-subsist":{"ag-subsist":.03046,"ind-alim":.30266,"biens-cons":.00206,"services":.04120},
"ag-exp+ind":{"ag-exp+ind":.01518,"ind-alim":.02043,"biens-cons":.01123,"biens-int":.00669},
"sylvicult":{"ind-alim":.00243,"biens-int":.02106},
"ind-alim":{"ag-subsist":.00341,"ag-exp+ind":.00629,"ind-alim":.03241,"biens-cons":.01234,"biens-int":.00503,"services":.00092,"publiques":.01532},
"biens-cons":{"ind-alim":.00105,"biens-cons":.05385,"biens-int":.00435,"services":.00103,"publiques":.00338},
"biens-int":{"ag-subsist":.00676,"ag-exp+ind":.12385,"sylvicult":.02095,"ind-alim":.03794,"biens-cons":.08309,"biens-int":.23461,"cim-int":.18289,"biens-cap":.01567,"construct":.14665,"services":.00929,"publiques":.08466},
"cim-int":{"ag-subsist":.00002,"ag-exp+ind":.00025,"sylvicult":.00017,"ind-alim":.11238,"biens-cons":.05095,"biens-int":.05593,"cim-int":.27608,"biens-cap":.11722,"construct":.18643,"services":.00018},
"biens-cap":{"ag-subsist":.00041,"ag-exp+ind":.00971,"sylvicult":.02427,"ind-alim":.00931,"biens-cons":.01229,"biens-int":.05259,"cim-int":.02053,"biens-cap":.05013,"construct":.02622,"services":.00389},
"construct":{"ag-subsist":.00472,"ag-exp+ind":.00113,"sylvicult":.00318,"ind-alim":.10456,"biens-cons":.01831,"biens-int":.05302,"cim-int":.00172,"biens-cap":.00031,"construct":.01457,"services":.00385,"publiques":.00394},
"services":{"ag-subsist":.00375,"ag-exp+ind":.30649,"sylvicult":.26666,"ind-alim":.10100,"biens-cons":.26072,"biens-int":.23006,"cim-int":.11793,"biens-cap":.09922,"construct":.13692,"services":.13728,"publiques":.24145},
"publiques":{"ag-subsist":.00022,"ag-exp+ind":.00293,"sylvicult":.00327,"ind-alim":.00536,"biens-cons":.00539,"biens-int":.00957,"cim-int":.00486,"biens-cap":.00081,"construct":.00447,"services":.00219},
}
imat = {
"ag-subsist":{"ag-subsist":.23637},
"biens-cap":{"ag-subsist":.59530,"ag-exp+ind":.60608,"sylvicult":.63876,"ind-alim":.60608,"biens-cons":.78723,"biens-int":.63876,"cim-int":.63876,"biens-cap":.60608,"construct":.71728,"services":.17610,"publiques":.17610},
"construct":{"ag-subsist":.16833,"ag-exp+ind":.39392,"sylvicult":.36124,"ind-alim":.39392,"biens-cons":.21277,"biens-int":.36124,"cim-int":.36124,"biens-cap":.39392,"construct":.28272,"services":.82390,"publiques":.82390},
}
wdist = {
"ag-subsist":[1.01890,.71491,0],"ag-exp+ind":[.49556,.34774,.29222],
"sylvicult":[3.26280,2.28900,1.92320],"ind-alim":[1.45710,1.02230,.85902],
"biens-cons":[1.13350,.79531,.66829],"biens-int":[3.10740,2.18060,1.83230],
"cim-int":[6.32240,4.43640,3.72770],"biens-cap":[2.50350,1.75520,1.47580],
"construct":[2.92040,2.04920,1.72200],"services":[1.40390,.98502,.82776],
"publiques":[0,1.32630,1.11460],
}
xle = {
"ag-subsist":[1654.43,162.89,0],"ag-exp+ind":[399.93,45.50800,5.05700],
"sylvicult":[7.66200,1.78900,.59700],"ind-alim":[12.98900,9.43400,2.35800],
"biens-cons":[28.34400,37.46200,12.48800],"biens-int":[18.33100,16.55300,8.30000],
"cim-int":[1.45800,1.31700,.66000],"biens-cap":[3.11200,2.82000,1.20800],
"construct":[22.58400,28.46200,7.11600],"services":[121.20,125.8,61.96000],
"publiques":[0,83.029,32.77100],
}
ZR = ["m0","e0","xd0","k","depr","rhoc","rhot","eta","pd0","tm0","itax","cles","gles","kio","dstr","dst","id"]
zz = {
"m0":  [2.461,8.039,.023,17.961,37.062,138.57,49.616,134.72,0,74.439,0],
"e0":  [4.594,125.07,22.337,23.451,5.864,101.33,10.501,3.838,0,81.626,0],
"xd0": [330.480,131.45,29.503,72.024,118.430,284.38,34.169,10.298,174.12,615.79,163.98],
"k":   [495.730,170.89,73.760,140.0,236.870,853.13,102.51,20.600,435.29,769.73,180.36],
"depr":[.0246,.0472,.0244,.0144,.0212,.0335,.0335,.0111,.0232,.0637,.0637],
"rhoc":[1.5,.9,.4,1.25,1.25,.5,.75,.4,.4,.4,.4],
"rhot":[1.5,.9,.4,1.25,1.25,.5,.75,.4,.4,.4,.4],
"eta": [1.0,1.0,1.0,4.00,4.00,4.0,4.00,4.0,4.0,4.0,4.0],
"pd0": [1.0]*11,
"tm0": [.2205,.2330,.278,.3534,.3826,.1768,.2633,.268,0,0,0],
"itax":[.0020,.1910,.057,.038,.096,.026,.014,.029,.034,.076,0],
"cles":[.2744,.00445,0,.05599,.14099,.17738,0,0,.004,.31921,.02358],
"gles":[0,0,0,0,0,0,0,0,0,0,1.00],
"kio": [.11,.09,.06,.01,.04,.14,.02,.01,.08,.34,.100],
"dstr":[.012203,.026694,.034742,.044291,.059958,.012287,0,.042047,0,0,0],
"dst": [4.033,3.509,1.025,3.19,7.101,3.494,0,.433,0,0,0],
"id":  [6.710,0,0,0,0,0,0,113.36,138.13,0,0],
}
DATA_DIR = Path(__file__).resolve().parents[2] / "cge_core" / "models" / "camcge" / "data"


def validate_source_tables():
    """Validate the transcribed benchmark tables before writing any CSVs."""
    ls0 = {l: sum(xle[i][k] for i in I) for k, l in enumerate(LC)}
    assert abs(ls0["rural"] - 2270.04) < 1e-6
    assert abs(ls0["urban-unsk"] - 515.064) < 1e-6
    assert abs(ls0["urban-skil"] - 132.515) < 1e-6

    pva0 = {
        c: 1 - sum(io.get(r, {}).get(c, 0) for r in I)
        - zz["itax"][I.index(c)]
        for c in I
    }
    assert abs(pva0["ag-subsist"] - 0.94825) < 1e-4

    assert abs(sum(zz["cles"]) - 1) < 1e-9
    assert abs(sum(zz["gles"]) - 1) < 1e-9
    assert abs(sum(zz["kio"]) - 1) < 1e-9

    for c in I:
        investment_column = (
            imat.get("ag-subsist", {}).get(c, 0)
            + imat["biens-cap"][c]
            + imat["construct"][c]
        )
        assert abs(investment_column - 1) < 1e-5
    return ls0


def write_data(data_dir=DATA_DIR):
    """Write CGE-Core CSV inputs and return the checked labor totals."""
    output_dir = Path(data_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    def wset(name, members):
        # The engine's DataPortal set loader treats the first row as a header.
        path = output_dir / f"set-{name}-.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow([name])
            writer.writerows([member] for member in members)

    def wmat(name, header0, cols, rows, get):
        path = output_dir / f"param-{name}-.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow([header0] + cols)
            for row in rows:
                writer.writerow([row] + [get(row, col) for col in cols])

    ls0 = validate_source_tables()
    wset("i", I)
    wset("lc", LC)
    wset("zrow", ZR)
    wmat("io", "IO", I, I, lambda r, c: io.get(r, {}).get(c, 0))
    wmat("imat", "IMAT", I, I, lambda r, c: imat.get(r, {}).get(c, 0))
    wmat("wdist", "WDIST", LC, I, lambda r, c: wdist[r][LC.index(c)])
    wmat("xle", "XLE", LC, I, lambda r, c: xle[r][LC.index(c)])
    wmat("zz", "ZZ", I, ZR, lambda r, c: zz[r][I.index(c)])
    return ls0


def main():
    ls0 = write_data()
    print(
        "data written; adding-up checks passed; ls0 =",
        {key: round(value, 3) for key, value in ls0.items()},
    )


if __name__ == "__main__":
    main()
