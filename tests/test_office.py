import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from office.agent import BaseAgent
from office.product import ProductSpec
from office.virtual_office import VirtualOffice


def make_query_fn(texts):
    """Crea una query_fn asincrona che restituisce, ad ogni chiamata, un
    messaggio in stile ResultMessage (con attributo `result`) preso in
    sequenza dalla lista `texts`. Emula claude_agent_sdk.query senza CLI."""
    remaining = list(texts)

    def query_fn(prompt, system_prompt, model):
        text = remaining.pop(0)

        async def _gen():
            yield SimpleNamespace(result=text)

        return _gen()

    return query_fn


class BaseAgentTests(unittest.TestCase):
    def test_respond_parses_lezione_and_updates_memory(self):
        agent = BaseAgent(
            name="Test",
            role="Tester",
            system_prompt="Sei un tester.",
            query_fn=make_query_fn(["Contenuto della risposta.\nLEZIONE: essere piu' concisi"]),
        )

        reply = agent.respond("prompt")

        self.assertIn("Contenuto della risposta.", reply)
        self.assertEqual(agent.memory.experience, 1)
        self.assertEqual(agent.memory.learnings, ["essere piu' concisi"])

    def test_respond_falls_back_to_assistant_text_blocks(self):
        # Nessun ResultMessage: solo blocchi di testo dell'assistente.
        def query_fn(prompt, system_prompt, model):
            async def _gen():
                yield SimpleNamespace(content=[SimpleNamespace(text="Ciao "), SimpleNamespace(text="mondo")])

            return _gen()

        agent = BaseAgent(name="T", role="R", system_prompt="x", query_fn=query_fn)
        self.assertEqual(agent.respond("p"), "Ciao mondo")

    def test_memory_keeps_only_recent_learnings(self):
        memory_agent = BaseAgent(name="Test", role="Tester", system_prompt="x", query_fn=make_query_fn([]))
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
        office = VirtualOffice(query_fn=make_query_fn(texts), viability_threshold=90.0, max_rounds=3)

        session = office.run("Un'app per la gestione fiscale delle PMI")

        self.assertEqual(len(session.rounds), 1)
        self.assertEqual(session.product.name, "Prodotto Test")
        self.assertEqual(session.product.version, 1)
        self.assertEqual(session.product.viability_score, 95.0)

    def test_progress_callback_invoked_for_each_role(self):
        texts = [
            "Proposta.\nLEZIONE: n1",
            "Analisi.\nLEZIONE: n2",
            "Piano.\nLEZIONE: n3",
            "Critica.\nPUNTEGGIO: 95\nLEZIONE: n4",
            '{"name": "Prodotto Test"}\nLEZIONE: n5',
        ]
        office = VirtualOffice(query_fn=make_query_fn(texts), viability_threshold=90.0, max_rounds=1)

        seen = []
        office.run("idea", progress_callback=lambda rnd, role, agent, text: seen.append((rnd, role)))

        self.assertEqual(
            seen,
            [(1, "strategist"), (1, "engineer"), (1, "marketer"), (1, "optimizer"), (1, "coordinator")],
        )

    def test_write_report_creates_markdown_file(self):
        texts = [
            "Proposta.\nLEZIONE: n1",
            "Analisi.\nLEZIONE: n2",
            "Piano.\nLEZIONE: n3",
            "Critica.\nPUNTEGGIO: 40\nLEZIONE: n4",
            '{"name": "Prodotto Beta"}\nLEZIONE: n5',
        ]
        office = VirtualOffice(query_fn=make_query_fn(texts), viability_threshold=90.0, max_rounds=1)
        session = office.run("idea di test")

        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = office.write_report(session, output_dir=tmp_dir)
            content = path.read_text(encoding="utf-8")

        self.assertIn("Prodotto Beta", content)
        self.assertIn("Cronologia dei cicli di collaborazione", content)


if __name__ == "__main__":
    unittest.main()
