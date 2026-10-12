import csv,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'coleta'))
from preparar_dataset import validate,windows,export,label
from simular_sensor_cp2 import generate

class DatasetTests(unittest.TestCase):
    def setUp(self):
        scratch=Path.cwd()/'work'/'test_tmp';scratch.mkdir(parents=True,exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(dir=scratch);self.p=Path(self.tmp.name)
        self.csv=self.p/'simulado.csv';generate(self.csv)
    def tearDown(self):self.tmp.cleanup()
    def write(self,rows):
        with self.csv.open('w',newline='') as f:
            w=csv.writer(f);w.writerow(['tempo_ms','distancia_cm','classe']);w.writerows(rows)
    def test_boundaries(self):
        self.assertEqual([label(x) for x in [24.99,25,60,60.01]],['PERIGO','ATENCAO','ATENCAO','LIVRE'])
    def test_fixture(self):self.assertEqual(len(validate(self.csv)),450)
    def test_missing(self):
        self.write([[0,'','LIVRE']]);self.assertRaises(ValueError,validate,self.csv)
    def test_nan(self):
        self.write([[0,'nan','LIVRE']]);self.assertRaises(ValueError,validate,self.csv)
    def test_invalid_range(self):
        self.write([[0,-1,'PERIGO']]);self.assertRaises(ValueError,validate,self.csv)
    def test_duplicates(self):
        self.write([[0,80,'LIVRE'],[0,80,'LIVRE']]);self.assertRaises(ValueError,validate,self.csv)
    def test_wrong_label(self):
        self.write([[0,20,'LIVRE']]);self.assertRaises(ValueError,validate,self.csv)
    def test_timestamp_reset(self):
        self.write([[150,80,'LIVRE'],[0,80,'LIVRE']]);self.assertRaises(ValueError,validate,self.csv)
    def test_gap_breaks_window(self):
        rows=[(i*150,80,'LIVRE') for i in range(10)];rows[5]=(900,80,'LIVRE')
        self.assertEqual(windows(rows),[])
    def test_split_and_format(self):
        r=export([(self.csv,None)],self.p/'out','simulado','temporal')
        self.assertEqual(r['janelas_por_subset_classe']['testing/PERIGO'],2)
        used={s:set() for s in ['training','testing']}
        for m in r['manifesto']:
            used[m['subset']].update(m['linhas'])
            with (self.p/'out'/m['arquivo']).open() as f:
                rr=list(csv.reader(f));self.assertEqual(rr[0],['timestamp','distancia_cm'])
                self.assertEqual(len(rr),11);self.assertEqual([int(x[0]) for x in rr[1:]],list(range(0,1500,150)))
        self.assertFalse(used['training']&used['testing'])
    def test_preserve_output(self):
        (self.p/'out').mkdir();self.assertRaises(ValueError,export,[(self.csv,None)],self.p/'out','simulado','temporal')
    def test_inadequate_dataset(self):
        self.write([[i*150,80,'LIVRE'] for i in range(10)])
        self.assertRaises(ValueError,export,[(self.csv,None)],self.p/'out','simulado','temporal')
    def test_no_cross_class_windows(self):
        for w in windows(validate(self.csv)):self.assertEqual(len({r[2] for _,r in w}),1)
    def test_reject_identical_windows_across_splits(self):
        self.write([[i*150,d,c] for i,(d,c) in enumerate([(80,'LIVRE')]*150+[(40,'ATENCAO')]*150+[(10,'PERIGO')]*150)])
        self.assertRaises(ValueError,export,[(self.csv,None)],self.p/'out','simulado','temporal')

if __name__=='__main__':unittest.main()
