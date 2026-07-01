import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from office.agent import BaseAgent
from office.product import ProductSpec
from office.virtual_office import VirtualOffice


def fake_client(texts):
    client = MagicMock()
    client.messages.create.side_effect = [
        SimpleNamespace(content=[SimpleNamespace(type="text", text=t)]) for t in texts
    ]
    return client


class BaseAgentTests(unittest.TestCase):
    def test_respond_parses_lezione_and_updates_memory(self):
        client = fake_client(["Contenuto della risposta.\nLEZIONE: essere piu' concisi"])
        agent = BaseAgent(name="Test", role="Tester", system_prompt="Sei un tester.", client=client)

        reply = agent.respond("prompt")

        self.assertIn("Contenuto della risposta.", reply)
        self.assertEqual(agent.memory.experience, 1)
        self.assertEqual(agent.memory.learnings, ["essere piu' concisi"])

    def test_memory_keeps_only_recent_learnings(self):
        memory_agent = BaseAgent(name="Test", role="Tester", system_prompt="x", client=MagicMock())
        for i in range(12):
            memory_agent.memory.add(f"nota-{i}")
        self.assertEqual(len(memory_agent.memory.learnings), 8)
        self.assertEqual(memory_agent.memory.learnings[-1], "nota-11")


class ProductSpecTests(unittest.TestCase):
    def test_apply_update_sets_fields_and_bumps_version(self):
        spec = ProductSpec()
        spec.apply_update(
            {
                "name": "Prodotto X",
                "key_features": ["a", "b"],
                "main_risks": [],
            }
        )
        self.assertEqual(spec.name, "Prodotto X")
        self.assertEqual(spec.key_features, ["a", "b"])
        self.assertEqual(spec.main_risks, [])
        self.assertEqual(spec.version, 1)


class VirtualOfficeTests(unittest.TestCase):
    def test_run_stops_early_when_viability_threshold_reached(self):
        texts = [
            "Proposta dello strategist.\nLEZIONE: nota-strategist",
            "Analisi dell'ingegnere.\nLEZIONE: nota-engineer",
            "Piano del marketer.\nLEZIONE: nota-marketer",
            "Critica dell'optimizer.\nPUNTEGGIO: 95\nLEZIONE: nota-optimizer",
            (
                '{"name": "Prodotto Test", "tagline": "Slogan", "description": "Descrizione",'
                ' "target_market": "PMI italiane", "key_features": ["f1", "f2"],'
                ' "pricing_model": "Abbonamento mensile", "revenue_strategy": "Upsell",'
                ' "differentiators": ["d1"], "main_risks": ["r1"]}\nLEZIONE: nota-coordinator'
            ),
        ]
        client = fake_client(texts)
        office = VirtualOffice(client=client, viability_threshold=90.0, max_rounds=3)

        session = office.run("Un'app per la gestione fiscale delle PMI")

        self.assertEqual(len(session.rounds), 1)
        self.assertEqual(session.product.name, "Prodotto Test")
        self.assertEqual(session.product.version, 1)
        self.assertEqual(session.product.viability_score, 95.0)

    def test_write_report_creates_markdown_file(self):
        texts = [
            "Proposta.\nLEZIONE: n1",
            "Analisi.\nLEZIONE: n2",
            "Piano.\nLEZIONE: n3",
            "Critica.\nPUNTEGGIO: 40\nLEZIONE: n4",
            '{"name": "Prodotto Beta"}\nLEZIONE: n5',
        ]
        client = fake_client(texts)
        office = VirtualOffice(client=client, viability_threshold=90.0, max_rounds=1)
        session = office.run("idea di test")

        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = office.write_report(session, output_dir=tmp_dir)
            content = path.read_text(encoding="utf-8")

        self.assertIn("Prodotto Beta", content)
        self.assertIn("Cronologia dei cicli di collaborazione", content)


if __name__ == "__main__":
    unittest.main()
