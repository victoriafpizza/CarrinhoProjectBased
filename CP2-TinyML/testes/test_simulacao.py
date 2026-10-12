import unittest,sys,json,math,csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'simulacao'))
from core import Simulation,run_scenario,TOPIC,parse_message
from inference import RuleEngine,EdgeImpulseONNX,real_availability
from policy_native import NativePolicy
class SimulationTests(unittest.TestCase):
    def test_json_valid(self):self.assertEqual(parse_message(TOPIC,'{"x":0,"y":255}'),(0,255))
    def test_json_bad_formats(self):
        for payload in ['[]','null','{','{"x":0}','{"x":true,"y":0}','{"x":256,"y":0}','{"x":"0","y":0}','{"x":0,"y":1.5}']:
            with self.subTest(payload=payload):self.assertRaises((ValueError,TypeError),parse_message,TOPIC,payload)
    def test_wrong_topic(self):self.assertRaises(ValueError,parse_message,'other','{"x":0,"y":0}')
    def test_rules_no_probability(self):
        for d,c in [(24.99,'PERIGO'),(25,'ATENCAO'),(60,'ATENCAO'),(60.01,'LIVRE')]:
            r=RuleEngine().predict([d]*10);self.assertEqual(r.label,c);self.assertIsNone(r.confidence);self.assertFalse(r.probabilities)
    def test_rules_invalid_window(self):
        for w in [[80]*9,[float('nan')]*10,[-1]*10,[500]*10]:self.assertRaises(ValueError,RuleEngine().predict,w)
    def test_startup_stopped(self):
        s=Simulation();s.receive(TOPIC,'{"x":0,"y":200}');s.step();self.assertEqual((s.left,s.right),(0,0))
    def test_scenario_livre(self):
        s=run_scenario('LIVRE');self.assertEqual((s.label,s.left,s.right),('LIVRE',200,200))
    def test_scenario_atencao(self):
        s=run_scenario('ATENCAO');self.assertEqual((s.label,s.left,s.right),('ATENCAO',100,100))
    def test_scenario_perigo(self):
        s=run_scenario('PERIGO');self.assertEqual((s.label,s.left,s.right),('PERIGO',0,0));self.assertEqual(s.position,0)
    def test_reverse(self):
        s=run_scenario('RE');self.assertEqual((s.left,s.right),(-100,-100));self.assertLess(s.position,0)
    def test_reverse_disabled(self):self.assertEqual(NativePolicy().gate(-200,-100,'PERIGO',True,False),(0,0))
    def test_pivot_blocked_in_perigo(self):self.assertEqual(NativePolicy().gate(200,-200,'PERIGO',True,True),(0,0))
    def test_invalid_sensor(self):
        s=run_scenario('SENSOR_INVALIDO');self.assertEqual((s.left,s.right),(0,0));self.assertEqual(s.label,'DESCONHECIDO')
    def test_low_confidence_fault(self):
        s=run_scenario('BAIXA_CONFIANCA');self.assertEqual((s.left,s.right),(0,0));self.assertIn('injetada',s.reason);self.assertIsNone(s.confidence)
    def test_disconnect(self):
        s=run_scenario('SEM_CONEXAO');self.assertEqual((s.left,s.right),(0,0))
    def test_timeout(self):
        s=run_scenario('LIVRE');s.time_ms+=351;s.actuate();self.assertEqual((s.left,s.right),(0,0))
    def test_bad_payload_stops(self):
        s=run_scenario('LIVRE');self.assertFalse(s.receive(TOPIC,'{}'));s.actuate();self.assertEqual((s.left,s.right),(0,0))
    def test_prediction_timeout(self):
        s=run_scenario('LIVRE');s.time_ms+=1801;s.receive(TOPIC,'{"x":0,"y":200}');s.actuate();self.assertEqual((s.left,s.right),(0,0))
    def test_clock_wraparound(self):self.assertTrue(NativePolicy().fresh(20,0xfffffff0,50))
    def test_differential_saturation(self):
        s=run_scenario('LIVRE');s.receive(TOPIC,'{"x":255,"y":255}');s.actuate();self.assertEqual((s.left,s.right),(255,0))
    def test_cxx_truncation_negative(self):self.assertEqual(NativePolicy().gate(-101,-99,'PERIGO',True),(-50,-49))
    def test_inverted_forward(self):self.assertEqual(NativePolicy().gate(-200,-100,'ATENCAO',True,True,-1),(-100,-50))
    def test_recovery_requires_whole_window(self):
        s=run_scenario('LIVRE');s.sensor(-1)
        for _ in range(9):s.sensor(100)
        s.actuate();self.assertEqual((s.left,s.right),(0,0));s.sensor(100);s.actuate();self.assertEqual((s.left,s.right),(200,200))
    def test_approach_trace(self):
        s=run_scenario('APROXIMACAO');classes={r['classe'] for r in s.trace};self.assertTrue({'LIVRE','ATENCAO','PERIGO'}<=classes);self.assertEqual(s.left,0)
    def test_four_motors_follow_sides(self):
        s=run_scenario('ATENCAO').snapshot();self.assertEqual(s['DE'],s['TE']);self.assertEqual(s['DD'],s['TD'])
    def test_real_unavailable_no_fallback(self):
        s=Simulation('B');
        if s.engine is not None:return
        for _ in range(10):s.sensor(100)
        self.assertEqual(s.label,'DESCONHECIDO');self.assertFalse(s.prediction_ok)
class RealModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine,reason=real_availability()
        if cls.engine is None:raise unittest.SkipTest('Modelo/runtime real indisponível: '+reason)
    def test_real_six_reserved_windows(self):
        for f in (ROOT/'dataset/teste').glob('*.csv'):
            with f.open() as stream:w=[float(r['distancia_cm']) for r in csv.DictReader(stream)]
            result=self.engine.predict(w)
            with self.subTest(f=f.name):
                self.assertEqual(result.label,f.name.split('.')[0]);self.assertAlmostEqual(sum(result.probabilities.values()),1,places=4)
    def test_real_scenarios(self):
        for name,expected in [('LIVRE',(200,200)),('ATENCAO',(100,100)),('PERIGO',(0,0)),('RE',(-100,-100))]:
            with self.subTest(name=name):
                s=run_scenario(name,'B');self.assertEqual(s.label,'PERIGO' if name=='RE' else name);self.assertEqual((s.left,s.right),expected);self.assertIsNotNone(s.confidence)
    def test_real_invalid_input(self):self.assertRaises(ValueError,self.engine.predict,[float('nan')]*10)
if __name__=='__main__':unittest.main()
