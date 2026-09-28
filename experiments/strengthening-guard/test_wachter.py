"""Verzonnen zinnen: wat de wachter moet zien, en wat hij met rust moet laten."""
import unittest
from wachter import compare

def kinds(src, tel):
    return sorted({k for r in compare(src, tel) for k, _ in r["vlaggen"]})

class Ziet(unittest.TestCase):
    def test_voorbehoud_weg(self):
        self.assertIn("VOORBEHOUD_WEG", kinds("- The cache may reduce load on some machines, untested.", "- The cache reduces load on machines."))
    def test_nl_voorbehoud_weg(self):
        self.assertIn("VOORBEHOUD_WEG", kinds("- Dit lijkt misschien op de oude kaart.", "- Dit is de oude kaart van de spinnen."))
    def test_ontkenning_weg(self):
        self.assertIn("ONTKENNING_WEG", kinds("- The report does not prove who merged the branch.", "- The report proves who merged the branch."))
    def test_trede_omhoog(self):
        self.assertIn("TREDE_OMHOOG", kinds("- This relation is a candidate from one chat.", "- This relation is established from one chat."))
    def test_identiteit(self):
        self.assertIn("TREDE_OMHOOG", kinds("- Het archief lijkt op de oude kaart in de tekst.", "- Het archief is hetzelfde als de oude kaart in de tekst."))
    def test_reikwijdte(self):
        self.assertIn("REIKWIJDTE_OMHOOG", kinds("- Some sessions dropped hedges when shortening notes.", "- All sessions dropped hedges when shortening notes."))
    def test_getal(self):
        self.assertIn("GETAL_ANDERS", kinds("- current/: 8 of 10 files rebuilt byte for byte.", "- current/: 9 of 10 files rebuilt byte for byte."))
    def test_notitie_weg(self):
        self.assertIn("NOTITIE_WEG_MET_VOORBEHOUD", kinds("- Whether the platform keeps a copy is untested.\n- Other note here stays.", "- Other note here stays."))

class LaatMetRust(unittest.TestCase):
    def test_zelfde_tekst(self):
        self.assertEqual(kinds("- The cache may help on some machines.", "- The cache may help on some machines."), [])
    def test_sterker_voorbehoud_is_geen_vlag(self):
        self.assertEqual(kinds("- The cache helps on machines.", "- The cache may help on some machines."), [])
    def test_herformuleren_zonder_verlies(self):
        self.assertEqual(kinds("- It was not tested whether the hook runs.", "- Whether the hook runs was not tested."), [])

if __name__ == "__main__":
    unittest.main()
