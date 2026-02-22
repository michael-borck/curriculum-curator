"""
QTI (Question and Test Interoperability) service for quiz import/export.

Supports:
- **QTI 1.2** export for IMSCC embedding (CC v1.1 compatibility, Canvas)
- **QTI 2.1** export as standalone ZIP for LMS quiz banks (Blackboard, Moodle)
- **QTI 1.2 + 2.1** import from IMSCC/SCORM packages with auto-version detection

Question type mapping:
- MULTIPLE_CHOICE, TRUE_FALSE → choiceInteraction / render_choice
- SHORT_ANSWER, FILL_IN_BLANK → textEntryInteraction / render_fib
- LONG_ANSWER, CASE_STUDY, SCENARIO → extendedTextInteraction / render_fib(rows=15)
- MATCHING → matchInteraction / multiple response_lid
"""

from __future__ import annotations

import logging
import uuid
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from io import BytesIO, StringIO
from typing import Any

from app.models.quiz_question import QuestionType, QuizQuestion

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# QTI namespaces
# ---------------------------------------------------------------------------

NS_QTI12 = "http://www.imsglobal.org/xsd/ims_qtiasiv1p2"
NS_QTI21 = "http://www.imsglobal.org/xsd/imsqti_v2p1"
NS_IMSCP = "http://www.imsglobal.org/xsd/imscp_v1p1"
NS_IMSMD = "http://www.imsglobal.org/xsd/imsmd_v1p2"

# Question types that map to essay / extendedText
_ESSAY_TYPES = {
    QuestionType.LONG_ANSWER.value,
    QuestionType.CASE_STUDY.value,
    QuestionType.SCENARIO.value,
}

# Question types that map to text entry / fill-in-blank
_TEXT_ENTRY_TYPES = {
    QuestionType.SHORT_ANSWER.value,
    QuestionType.FILL_IN_BLANK.value,
}


# ---------------------------------------------------------------------------
# ParsedQuestion — intermediate dataclass for import
# ---------------------------------------------------------------------------


def _extract_mattext(parent: ET.Element) -> str:
    """Extract text from material/mattext child of an element."""
    mat = parent.find("material")
    if mat is not None:
        mt = mat.find("mattext")
        if mt is not None and mt.text:
            return mt.text.strip()
    return ""


@dataclass
class ParsedQuestion:
    """Intermediate representation of a parsed QTI question."""

    question_text: str
    question_type: str  # QuestionType enum value
    options: list[dict[str, Any]] = field(default_factory=list)
    correct_answers: list[str] = field(default_factory=list)
    feedback: dict[str, Any] | None = None
    answer_explanation: str | None = None
    points: float = 1.0
    order_index: int = 0


# ---------------------------------------------------------------------------
# QTI Exporter
# ---------------------------------------------------------------------------


class QTIExporter:
    """Exports QuizQuestion rows to QTI 1.2 and QTI 2.1 XML."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def export_qti12(self, questions: list[QuizQuestion], title: str) -> str:
        """Export questions as a QTI 1.2 XML string (for IMSCC embedding)."""
        root = ET.Element("questestinterop")
        assessment = ET.SubElement(
            root,
            "assessment",
            ident=f"assessment_{uuid.uuid4().hex[:8]}",
            title=title,
        )
        section = ET.SubElement(
            assessment,
            "section",
            ident="root_section",
            title="Default",
        )

        for q in questions:
            q_type = str(q.question_type)
            if q_type in (
                QuestionType.MULTIPLE_CHOICE.value,
                QuestionType.TRUE_FALSE.value,
            ):
                self._mc_to_qti12(section, q)
            elif q_type in _TEXT_ENTRY_TYPES:
                self._text_entry_to_qti12(section, q)
            elif q_type in _ESSAY_TYPES:
                self._essay_to_qti12(section, q)
            elif q_type == QuestionType.MATCHING.value:
                self._matching_to_qti12(section, q)
            else:
                logger.warning("Unsupported question type for QTI 1.2: %s", q_type)

        tree = ET.ElementTree(root)
        buf = StringIO()
        tree.write(buf, encoding="unicode", xml_declaration=True)
        return buf.getvalue()

    def export_qti21_zip(self, questions: list[QuizQuestion], title: str) -> BytesIO:
        """Export questions as a QTI 2.1 package ZIP (standalone)."""
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            item_refs: list[tuple[str, str]] = []  # (identifier, href)

            for _i, q in enumerate(questions):
                ident = f"item_{uuid.uuid4().hex[:8]}"
                href = f"{ident}.xml"
                item_xml = self._question_to_qti21(q, ident)
                if item_xml is not None:
                    zf.writestr(href, item_xml)
                    item_refs.append((ident, href))

            # Write imsmanifest.xml
            manifest = self._build_qti21_manifest(title, item_refs)
            zf.writestr("imsmanifest.xml", manifest)

        buf.seek(0)
        return buf

    # ------------------------------------------------------------------
    # QTI 1.2 private methods
    # ------------------------------------------------------------------

    def _mc_to_qti12(self, section: ET.Element, q: QuizQuestion) -> None:
        """Multiple choice / true-false → QTI 1.2."""
        ident = f"q_{uuid.uuid4().hex[:8]}"
        item = ET.SubElement(
            section, "item", ident=ident, title=str(q.question_text)[:80]
        )

        # Presentation
        presentation = ET.SubElement(item, "presentation")
        material = ET.SubElement(presentation, "material")
        mattext = ET.SubElement(material, "mattext", texttype="text/html")
        mattext.text = str(q.question_text)

        response_lid = ET.SubElement(
            presentation,
            "response_lid",
            ident="response1",
            rcardinality="Single",
        )
        render_choice = ET.SubElement(response_lid, "render_choice")

        options = q.options or []
        correct = q.correct_answers or []
        option_idents: list[str] = []

        for j, opt in enumerate(options):
            opt_ident = f"opt_{j}"
            option_idents.append(opt_ident)
            response_label = ET.SubElement(
                render_choice, "response_label", ident=opt_ident
            )
            mat = ET.SubElement(response_label, "material")
            mt = ET.SubElement(mat, "mattext", texttype="text/html")
            mt.text = str(opt) if isinstance(opt, str) else str(opt.get("text", opt))

        # Response processing
        resprocessing = ET.SubElement(item, "resprocessing")
        outcomes = ET.SubElement(resprocessing, "outcomes")
        ET.SubElement(
            outcomes,
            "decvar",
            maxvalue=str(q.points),
            minvalue="0",
            varname="SCORE",
            vartype="Decimal",
        )

        # Map correct answers to option indices
        for j, opt in enumerate(options):
            opt_text = str(opt) if isinstance(opt, str) else str(opt.get("text", opt))
            if opt_text in correct or str(j) in [str(c) for c in correct]:
                respcondition = ET.SubElement(
                    resprocessing, "respcondition", continuealiasYes="No"
                )
                conditionvar = ET.SubElement(respcondition, "conditionvar")
                ET.SubElement(
                    conditionvar, "varequal", respident="response1"
                ).text = f"opt_{j}"
                ET.SubElement(
                    respcondition, "setvar", action="Set", varname="SCORE"
                ).text = str(q.points)

        self._add_feedback_qti12(item, q)

    def _text_entry_to_qti12(self, section: ET.Element, q: QuizQuestion) -> None:
        """Short answer / fill-in-blank → QTI 1.2."""
        ident = f"q_{uuid.uuid4().hex[:8]}"
        item = ET.SubElement(
            section, "item", ident=ident, title=str(q.question_text)[:80]
        )

        presentation = ET.SubElement(item, "presentation")
        material = ET.SubElement(presentation, "material")
        mattext = ET.SubElement(material, "mattext", texttype="text/html")
        mattext.text = str(q.question_text)

        response_str = ET.SubElement(
            presentation, "response_str", ident="response1", rcardinality="Single"
        )
        ET.SubElement(response_str, "render_fib")

        # Response processing
        resprocessing = ET.SubElement(item, "resprocessing")
        outcomes = ET.SubElement(resprocessing, "outcomes")
        ET.SubElement(
            outcomes,
            "decvar",
            maxvalue=str(q.points),
            minvalue="0",
            varname="SCORE",
            vartype="Decimal",
        )

        correct = q.correct_answers or []
        for ans in correct:
            respcondition = ET.SubElement(
                resprocessing, "respcondition", continuealiasYes="No"
            )
            conditionvar = ET.SubElement(respcondition, "conditionvar")
            ET.SubElement(conditionvar, "varequal", respident="response1").text = str(
                ans
            )
            ET.SubElement(
                respcondition, "setvar", action="Set", varname="SCORE"
            ).text = str(q.points)

        self._add_feedback_qti12(item, q)

    def _essay_to_qti12(self, section: ET.Element, q: QuizQuestion) -> None:
        """Long answer / case study / scenario → QTI 1.2."""
        ident = f"q_{uuid.uuid4().hex[:8]}"
        item = ET.SubElement(
            section, "item", ident=ident, title=str(q.question_text)[:80]
        )

        presentation = ET.SubElement(item, "presentation")
        material = ET.SubElement(presentation, "material")
        mattext = ET.SubElement(material, "mattext", texttype="text/html")
        mattext.text = str(q.question_text)

        response_str = ET.SubElement(
            presentation, "response_str", ident="response1", rcardinality="Single"
        )
        ET.SubElement(response_str, "render_fib", rows="15", columns="60")

        self._add_feedback_qti12(item, q)

    def _matching_to_qti12(self, section: ET.Element, q: QuizQuestion) -> None:
        """Matching → QTI 1.2 (one response_lid per left item)."""
        ident = f"q_{uuid.uuid4().hex[:8]}"
        item = ET.SubElement(
            section, "item", ident=ident, title=str(q.question_text)[:80]
        )

        presentation = ET.SubElement(item, "presentation")
        material = ET.SubElement(presentation, "material")
        mattext = ET.SubElement(material, "mattext", texttype="text/html")
        mattext.text = str(q.question_text)

        options = q.options or []

        # Each option is a pair: {"left": ..., "right": ...}
        right_values: list[str] = []
        for opt in options:
            if isinstance(opt, dict):
                right_val = str(opt.get("right", ""))
                if right_val and right_val not in right_values:
                    right_values.append(right_val)

        for i, opt in enumerate(options):
            if not isinstance(opt, dict):
                continue
            left_text = str(opt.get("left", f"Item {i + 1}"))
            resp_ident = f"response_{i}"

            response_lid = ET.SubElement(
                presentation, "response_lid", ident=resp_ident, rcardinality="Single"
            )
            # Show the left item as the prompt
            mat = ET.SubElement(response_lid, "material")
            mt = ET.SubElement(mat, "mattext", texttype="text/html")
            mt.text = left_text

            render_choice = ET.SubElement(response_lid, "render_choice")
            for j, rv in enumerate(right_values):
                rl = ET.SubElement(render_choice, "response_label", ident=f"match_{j}")
                rm = ET.SubElement(rl, "material")
                rmt = ET.SubElement(rm, "mattext", texttype="text/html")
                rmt.text = rv

        # Response processing
        resprocessing = ET.SubElement(item, "resprocessing")
        outcomes = ET.SubElement(resprocessing, "outcomes")
        ET.SubElement(
            outcomes,
            "decvar",
            maxvalue=str(q.points),
            minvalue="0",
            varname="SCORE",
            vartype="Decimal",
        )

        for i, opt in enumerate(options):
            if not isinstance(opt, dict):
                continue
            right_val = str(opt.get("right", ""))
            if right_val in right_values:
                match_idx = right_values.index(right_val)
                respcondition = ET.SubElement(resprocessing, "respcondition")
                conditionvar = ET.SubElement(respcondition, "conditionvar")
                ET.SubElement(
                    conditionvar, "varequal", respident=f"response_{i}"
                ).text = f"match_{match_idx}"

        self._add_feedback_qti12(item, q)

    def _add_feedback_qti12(self, item: ET.Element, q: QuizQuestion) -> None:
        """Add feedback / answer explanation to a QTI 1.2 item."""
        explanation = q.answer_explanation
        if not explanation:
            return
        itemfeedback = ET.SubElement(item, "itemfeedback", ident="general_feedback")
        flow_mat = ET.SubElement(itemfeedback, "flow_mat")
        material = ET.SubElement(flow_mat, "material")
        mattext = ET.SubElement(material, "mattext", texttype="text/html")
        mattext.text = str(explanation)

    # ------------------------------------------------------------------
    # QTI 2.1 private methods
    # ------------------------------------------------------------------

    def _question_to_qti21(self, q: QuizQuestion, ident: str) -> str | None:
        """Convert a single question to QTI 2.1 assessmentItem XML string."""
        q_type = str(q.question_type)

        if q_type in (
            QuestionType.MULTIPLE_CHOICE.value,
            QuestionType.TRUE_FALSE.value,
        ):
            return self._mc_to_qti21(q, ident)
        if q_type in _TEXT_ENTRY_TYPES:
            return self._text_entry_to_qti21(q, ident)
        if q_type in _ESSAY_TYPES:
            return self._essay_to_qti21(q, ident)
        if q_type == QuestionType.MATCHING.value:
            return self._matching_to_qti21(q, ident)

        logger.warning("Unsupported question type for QTI 2.1: %s", q_type)
        return None

    def _mc_to_qti21(self, q: QuizQuestion, ident: str) -> str:
        """Multiple choice / true-false → QTI 2.1 assessmentItem."""
        ET.register_namespace("", NS_QTI21)
        item = ET.Element(
            f"{{{NS_QTI21}}}assessmentItem",
            identifier=ident,
            title=str(q.question_text)[:80],
            adaptive="false",
            timeDependent="false",
        )

        options = q.options or []
        correct = q.correct_answers or []

        # Find correct option identifier
        correct_ident = "opt_0"
        for j, opt in enumerate(options):
            opt_text = str(opt) if isinstance(opt, str) else str(opt.get("text", opt))
            if opt_text in correct or str(j) in [str(c) for c in correct]:
                correct_ident = f"opt_{j}"
                break

        # responseDeclaration
        resp_decl = ET.SubElement(
            item,
            f"{{{NS_QTI21}}}responseDeclaration",
            identifier="RESPONSE",
            cardinality="single",
            baseType="identifier",
        )
        correct_resp = ET.SubElement(resp_decl, f"{{{NS_QTI21}}}correctResponse")
        ET.SubElement(correct_resp, f"{{{NS_QTI21}}}value").text = correct_ident

        # outcomeDeclaration
        ET.SubElement(
            item,
            f"{{{NS_QTI21}}}outcomeDeclaration",
            identifier="SCORE",
            cardinality="single",
            baseType="float",
        )

        # itemBody
        body = ET.SubElement(item, f"{{{NS_QTI21}}}itemBody")
        choice_interaction = ET.SubElement(
            body,
            f"{{{NS_QTI21}}}choiceInteraction",
            responseIdentifier="RESPONSE",
            shuffle="false",
            maxChoices="1",
        )
        prompt = ET.SubElement(choice_interaction, f"{{{NS_QTI21}}}prompt")
        prompt.text = str(q.question_text)

        for j, opt in enumerate(options):
            opt_text = str(opt) if isinstance(opt, str) else str(opt.get("text", opt))
            choice = ET.SubElement(
                choice_interaction,
                f"{{{NS_QTI21}}}simpleChoice",
                identifier=f"opt_{j}",
            )
            choice.text = opt_text

        # responseProcessing
        resp_proc = ET.SubElement(item, f"{{{NS_QTI21}}}responseProcessing")
        resp_cond = ET.SubElement(resp_proc, f"{{{NS_QTI21}}}responseCondition")
        resp_if = ET.SubElement(resp_cond, f"{{{NS_QTI21}}}responseIf")
        match = ET.SubElement(resp_if, f"{{{NS_QTI21}}}match")
        ET.SubElement(match, f"{{{NS_QTI21}}}variable", identifier="RESPONSE")
        ET.SubElement(match, f"{{{NS_QTI21}}}correct", identifier="RESPONSE")
        set_val = ET.SubElement(
            resp_if, f"{{{NS_QTI21}}}setOutcomeValue", identifier="SCORE"
        )
        ET.SubElement(set_val, f"{{{NS_QTI21}}}baseValue", baseType="float").text = str(
            q.points
        )

        return self._serialize_element(item)

    def _text_entry_to_qti21(self, q: QuizQuestion, ident: str) -> str:
        """Short answer / fill-in-blank → QTI 2.1 assessmentItem."""
        ET.register_namespace("", NS_QTI21)
        item = ET.Element(
            f"{{{NS_QTI21}}}assessmentItem",
            identifier=ident,
            title=str(q.question_text)[:80],
            adaptive="false",
            timeDependent="false",
        )

        correct = q.correct_answers or []

        # responseDeclaration
        resp_decl = ET.SubElement(
            item,
            f"{{{NS_QTI21}}}responseDeclaration",
            identifier="RESPONSE",
            cardinality="single",
            baseType="string",
        )
        if correct:
            correct_resp = ET.SubElement(resp_decl, f"{{{NS_QTI21}}}correctResponse")
            ET.SubElement(correct_resp, f"{{{NS_QTI21}}}value").text = str(correct[0])

        ET.SubElement(
            item,
            f"{{{NS_QTI21}}}outcomeDeclaration",
            identifier="SCORE",
            cardinality="single",
            baseType="float",
        )

        body = ET.SubElement(item, f"{{{NS_QTI21}}}itemBody")
        p = ET.SubElement(body, f"{{{NS_QTI21}}}p")
        p.text = str(q.question_text)
        ET.SubElement(
            body,
            f"{{{NS_QTI21}}}textEntryInteraction",
            responseIdentifier="RESPONSE",
            expectedLength="50",
        )

        return self._serialize_element(item)

    def _essay_to_qti21(self, q: QuizQuestion, ident: str) -> str:
        """Long answer / case study / scenario → QTI 2.1 assessmentItem."""
        ET.register_namespace("", NS_QTI21)
        item = ET.Element(
            f"{{{NS_QTI21}}}assessmentItem",
            identifier=ident,
            title=str(q.question_text)[:80],
            adaptive="false",
            timeDependent="false",
        )

        ET.SubElement(
            item,
            f"{{{NS_QTI21}}}responseDeclaration",
            identifier="RESPONSE",
            cardinality="single",
            baseType="string",
        )
        ET.SubElement(
            item,
            f"{{{NS_QTI21}}}outcomeDeclaration",
            identifier="SCORE",
            cardinality="single",
            baseType="float",
        )

        body = ET.SubElement(item, f"{{{NS_QTI21}}}itemBody")
        p = ET.SubElement(body, f"{{{NS_QTI21}}}p")
        p.text = str(q.question_text)
        ET.SubElement(
            body,
            f"{{{NS_QTI21}}}extendedTextInteraction",
            responseIdentifier="RESPONSE",
            expectedLines="15",
        )

        return self._serialize_element(item)

    def _matching_to_qti21(self, q: QuizQuestion, ident: str) -> str:
        """Matching → QTI 2.1 matchInteraction."""
        ET.register_namespace("", NS_QTI21)
        item = ET.Element(
            f"{{{NS_QTI21}}}assessmentItem",
            identifier=ident,
            title=str(q.question_text)[:80],
            adaptive="false",
            timeDependent="false",
        )

        options = q.options or []

        ET.SubElement(
            item,
            f"{{{NS_QTI21}}}responseDeclaration",
            identifier="RESPONSE",
            cardinality="multiple",
            baseType="directedPair",
        )
        ET.SubElement(
            item,
            f"{{{NS_QTI21}}}outcomeDeclaration",
            identifier="SCORE",
            cardinality="single",
            baseType="float",
        )

        body = ET.SubElement(item, f"{{{NS_QTI21}}}itemBody")
        match_interaction = ET.SubElement(
            body,
            f"{{{NS_QTI21}}}matchInteraction",
            responseIdentifier="RESPONSE",
            shuffle="false",
        )
        prompt = ET.SubElement(match_interaction, f"{{{NS_QTI21}}}prompt")
        prompt.text = str(q.question_text)

        # Source set (left items)
        source_set = ET.SubElement(match_interaction, f"{{{NS_QTI21}}}simpleMatchSet")
        # Target set (right items)
        target_set = ET.SubElement(match_interaction, f"{{{NS_QTI21}}}simpleMatchSet")

        right_values: list[str] = []
        for i, opt in enumerate(options):
            if isinstance(opt, dict):
                left = str(opt.get("left", f"Item {i + 1}"))
                right = str(opt.get("right", ""))

                assoc = ET.SubElement(
                    source_set,
                    f"{{{NS_QTI21}}}simpleAssociableChoice",
                    identifier=f"src_{i}",
                    matchMax="1",
                )
                assoc.text = left

                if right and right not in right_values:
                    right_values.append(right)

        for j, rv in enumerate(right_values):
            assoc = ET.SubElement(
                target_set,
                f"{{{NS_QTI21}}}simpleAssociableChoice",
                identifier=f"tgt_{j}",
                matchMax="1",
            )
            assoc.text = rv

        return self._serialize_element(item)

    def _build_qti21_manifest(
        self, title: str, item_refs: list[tuple[str, str]]
    ) -> str:
        """Build imsmanifest.xml for a QTI 2.1 package."""
        ET.register_namespace("", NS_IMSCP)

        manifest = ET.Element(
            f"{{{NS_IMSCP}}}manifest",
            identifier=f"qti_manifest_{uuid.uuid4().hex[:8]}",
        )

        metadata = ET.SubElement(manifest, f"{{{NS_IMSCP}}}metadata")
        schema = ET.SubElement(metadata, f"{{{NS_IMSCP}}}schema")
        schema.text = "QTIv2.1 Package"
        schema_ver = ET.SubElement(metadata, f"{{{NS_IMSCP}}}schemaversion")
        schema_ver.text = "1.0.0"

        organizations = ET.SubElement(manifest, f"{{{NS_IMSCP}}}organizations")
        org = ET.SubElement(
            organizations, f"{{{NS_IMSCP}}}organization", identifier="org_1"
        )
        org_title = ET.SubElement(org, f"{{{NS_IMSCP}}}title")
        org_title.text = title

        resources = ET.SubElement(manifest, f"{{{NS_IMSCP}}}resources")
        for item_ident, href in item_refs:
            res = ET.SubElement(
                resources,
                f"{{{NS_IMSCP}}}resource",
                identifier=item_ident,
                type="imsqti_item_xmlv2p1",
                href=href,
            )
            ET.SubElement(res, f"{{{NS_IMSCP}}}file", href=href)

        tree = ET.ElementTree(manifest)
        buf = StringIO()
        tree.write(buf, encoding="unicode", xml_declaration=True)
        return buf.getvalue()

    @staticmethod
    def _serialize_element(elem: ET.Element) -> str:
        """Serialize an XML element to a string."""
        tree = ET.ElementTree(elem)
        buf = StringIO()
        tree.write(buf, encoding="unicode", xml_declaration=True)
        return buf.getvalue()


# ---------------------------------------------------------------------------
# QTI Importer
# ---------------------------------------------------------------------------


class QTIImporter:
    """Parses QTI XML (1.2 and 2.1) into ParsedQuestion dataclasses."""

    def parse_qti_from_zip(
        self, zf: zipfile.ZipFile
    ) -> list[tuple[str, list[ParsedQuestion]]]:
        """Scan a ZIP for QTI files, auto-detect version, parse all questions.

        Returns list of (filename, questions) tuples.
        """
        results: list[tuple[str, list[ParsedQuestion]]] = []

        for name in zf.namelist():
            if not name.endswith(".xml"):
                continue
            try:
                xml_bytes = zf.read(name)
                xml_text = xml_bytes.decode("utf-8", errors="replace")
                root = ET.fromstring(xml_text)
            except ET.ParseError:
                continue

            tag = root.tag.lower()

            # QTI 1.2: root is <questestinterop>
            if "questestinterop" in tag:
                questions = self._parse_qti12_assessment(root)
                if questions:
                    results.append((name, questions))

            # QTI 2.1: root is <assessmentItem> (individual item files)
            elif "assessmentitem" in tag:
                q = self._parse_qti21_item(root)
                if q is not None:
                    results.append((name, [q]))

            # QTI 2.1: root is <assessmentTest> — look for item refs
            elif "assessmenttest" in tag:
                # The items are in separate files; we'll pick them up individually
                continue

        return results

    # ------------------------------------------------------------------
    # QTI 1.2 parsing
    # ------------------------------------------------------------------

    def _parse_qti12_assessment(self, root: ET.Element) -> list[ParsedQuestion]:
        """Parse a QTI 1.2 <questestinterop> document."""
        questions: list[ParsedQuestion] = []
        order = 0

        # Find all <item> elements anywhere in the tree
        for item in root.iter("item"):
            q = self._parse_qti12_item(item)
            if q is not None:
                q.order_index = order
                questions.append(q)
                order += 1

        return questions

    def _parse_qti12_item(self, item: ET.Element) -> ParsedQuestion | None:
        """Parse a single QTI 1.2 <item> element."""
        # Extract question text from presentation/material/mattext
        question_text = ""
        presentation = item.find("presentation")
        if presentation is not None:
            mat = presentation.find("material")
            if mat is not None:
                mattext = mat.find("mattext")
                if mattext is not None and mattext.text:
                    question_text = mattext.text.strip()

        if not question_text:
            return None

        # Detect question type by looking at response elements
        if presentation is not None:
            response_lid = presentation.find("response_lid")
            response_str = presentation.find("response_str")

            if response_lid is not None:
                # Check if it's matching (multiple response_lid elements)
                all_lids = presentation.findall("response_lid")
                if len(all_lids) > 1:
                    return self._parse_qti12_matching(item, question_text, all_lids)
                return self._parse_qti12_choice(item, question_text, response_lid)

            if response_str is not None:
                render_fib = response_str.find("render_fib")
                if render_fib is not None:
                    rows = render_fib.get("rows", "1")
                    if int(rows) > 5:
                        return ParsedQuestion(
                            question_text=question_text,
                            question_type=QuestionType.LONG_ANSWER.value,
                        )
                    return self._parse_qti12_text_entry(item, question_text)

        return ParsedQuestion(
            question_text=question_text,
            question_type=QuestionType.SHORT_ANSWER.value,
        )

    def _parse_qti12_choice(
        self,
        item: ET.Element,
        question_text: str,
        response_lid: ET.Element,
    ) -> ParsedQuestion:
        """Parse a QTI 1.2 choice (MC/TF) item."""
        render_choice = response_lid.find("render_choice")
        options: list[dict[str, Any]] = []
        option_idents: dict[str, str] = {}  # ident -> text

        if render_choice is not None:
            for rl in render_choice.findall("response_label"):
                rl_ident = rl.get("ident", "")
                mat = rl.find("material")
                text = ""
                if mat is not None:
                    mt = mat.find("mattext")
                    if mt is not None and mt.text:
                        text = mt.text.strip()
                options.append({"text": text})
                option_idents[rl_ident] = text

        # Find correct answers from resprocessing
        correct_answers: list[str] = []
        resprocessing = item.find("resprocessing")
        if resprocessing is not None:
            for respcond in resprocessing.findall("respcondition"):
                condvar = respcond.find("conditionvar")
                setvar = respcond.find("setvar")
                if condvar is not None and setvar is not None:
                    score_text = setvar.text or "0"
                    try:
                        score = float(score_text)
                    except ValueError:
                        score = 0
                    if score > 0:
                        varequal = condvar.find("varequal")
                        if varequal is not None and varequal.text:
                            opt_text = option_idents.get(varequal.text, varequal.text)
                            correct_answers.append(opt_text)

        # Determine if true/false
        q_type = QuestionType.MULTIPLE_CHOICE.value
        if len(options) == 2:
            texts = {o["text"].lower() for o in options}
            if texts == {"true", "false"}:
                q_type = QuestionType.TRUE_FALSE.value

        # Extract feedback
        explanation = self._extract_feedback_qti12(item)

        return ParsedQuestion(
            question_text=question_text,
            question_type=q_type,
            options=options,
            correct_answers=correct_answers,
            answer_explanation=explanation,
        )

    def _parse_qti12_text_entry(
        self, item: ET.Element, question_text: str
    ) -> ParsedQuestion:
        """Parse a QTI 1.2 text entry (short answer/fill-in-blank) item."""
        correct_answers: list[str] = []
        resprocessing = item.find("resprocessing")
        if resprocessing is not None:
            for respcond in resprocessing.findall("respcondition"):
                condvar = respcond.find("conditionvar")
                if condvar is not None:
                    varequal = condvar.find("varequal")
                    if varequal is not None and varequal.text:
                        correct_answers.append(varequal.text)

        explanation = self._extract_feedback_qti12(item)

        return ParsedQuestion(
            question_text=question_text,
            question_type=QuestionType.SHORT_ANSWER.value,
            correct_answers=correct_answers,
            answer_explanation=explanation,
        )

    def _parse_qti12_matching(
        self,
        item: ET.Element,
        question_text: str,
        response_lids: list[ET.Element],
    ) -> ParsedQuestion:
        """Parse a QTI 1.2 matching item (multiple response_lid elements)."""
        options: list[dict[str, Any]] = []

        for lid in response_lids:
            left_text = _extract_mattext(lid)
            right_text = self._extract_first_choice_text(lid)
            if left_text:
                options.append({"left": left_text, "right": right_text})

        # Try to get correct pairings from resprocessing
        resprocessing = item.find("resprocessing")
        if resprocessing is not None:
            lid_choices = self._build_lid_choice_map(response_lids)
            self._apply_matching_correct_answers(resprocessing, lid_choices, options)

        return ParsedQuestion(
            question_text=question_text,
            question_type=QuestionType.MATCHING.value,
            options=options,
        )

    @staticmethod
    def _extract_first_choice_text(lid: ET.Element) -> str:
        """Extract the text of the first response_label in a response_lid."""
        render_choice = lid.find("render_choice")
        if render_choice is None:
            return ""
        first_label = render_choice.find("response_label")
        if first_label is None:
            return ""
        return _extract_mattext(first_label)

    @staticmethod
    def _build_lid_choice_map(
        response_lids: list[ET.Element],
    ) -> dict[str, dict[str, str]]:
        """Build a map: response_lid ident → {choice_ident: text}."""
        lid_choices: dict[str, dict[str, str]] = {}
        for lid in response_lids:
            lid_ident = lid.get("ident", "")
            render_choice = lid.find("render_choice")
            if render_choice is not None:
                choices: dict[str, str] = {}
                for rl in render_choice.findall("response_label"):
                    rl_ident = rl.get("ident", "")
                    choices[rl_ident] = _extract_mattext(rl)
                lid_choices[lid_ident] = choices
        return lid_choices

    @staticmethod
    def _apply_matching_correct_answers(
        resprocessing: ET.Element,
        lid_choices: dict[str, dict[str, str]],
        options: list[dict[str, Any]],
    ) -> None:
        """Resolve correct matching pairings from resprocessing."""
        for i, respcond in enumerate(resprocessing.findall("respcondition")):
            condvar = respcond.find("conditionvar")
            if condvar is None:
                continue
            varequal = condvar.find("varequal")
            if varequal is None:
                continue
            resp_ident = varequal.get("respident", "")
            chosen_ident = varequal.text or ""
            if (
                resp_ident in lid_choices
                and chosen_ident in lid_choices[resp_ident]
                and i < len(options)
            ):
                options[i]["right"] = lid_choices[resp_ident][chosen_ident]

    @staticmethod
    def _extract_feedback_qti12(item: ET.Element) -> str | None:
        """Extract feedback/explanation from a QTI 1.2 item."""
        for fb in item.findall("itemfeedback"):
            flow_mat = fb.find("flow_mat")
            if flow_mat is not None:
                mat = flow_mat.find("material")
                if mat is not None:
                    mt = mat.find("mattext")
                    if mt is not None and mt.text:
                        return mt.text.strip()
        return None

    # ------------------------------------------------------------------
    # QTI 2.1 parsing
    # ------------------------------------------------------------------

    def _parse_qti21_item(self, root: ET.Element) -> ParsedQuestion | None:
        """Parse a single QTI 2.1 <assessmentItem> element."""
        # Strip namespace for easier element finding
        ns = ""
        tag = root.tag
        if "}" in tag:
            ns = tag[: tag.index("}") + 1]

        def find(parent: ET.Element, local: str) -> ET.Element | None:
            return parent.find(f"{ns}{local}")

        def findall(parent: ET.Element, local: str) -> list[ET.Element]:
            return parent.findall(f"{ns}{local}")

        def find_deep(parent: ET.Element, local: str) -> ET.Element | None:
            return parent.find(f".//{ns}{local}")

        body = find(root, "itemBody")
        if body is None:
            return None

        # Detect interaction type
        choice = find_deep(body, "choiceInteraction")
        text_entry = find_deep(body, "textEntryInteraction")
        extended_text = find_deep(body, "extendedTextInteraction")
        match_int = find_deep(body, "matchInteraction")

        if choice is not None:
            return self._parse_qti21_choice(root, choice, ns)
        if match_int is not None:
            return self._parse_qti21_match(root, match_int, ns)
        if extended_text is not None:
            return self._parse_qti21_extended_text(root, body, ns)
        if text_entry is not None:
            return self._parse_qti21_text_entry(root, body, ns)

        return None

    def _parse_qti21_choice(
        self, root: ET.Element, interaction: ET.Element, ns: str
    ) -> ParsedQuestion:
        """Parse a QTI 2.1 choiceInteraction."""
        # Prompt text
        prompt_el = interaction.find(f"{ns}prompt")
        question_text = (
            prompt_el.text.strip() if prompt_el is not None and prompt_el.text else ""
        )

        # Options
        options: list[dict[str, Any]] = []
        option_idents: dict[str, str] = {}
        for sc in interaction.findall(f"{ns}simpleChoice"):
            ident = sc.get("identifier", "")
            text = sc.text.strip() if sc.text else ""
            options.append({"text": text})
            option_idents[ident] = text

        # Correct answer from responseDeclaration
        correct_answers: list[str] = []
        for rd in root.findall(f"{ns}responseDeclaration"):
            if rd.get("identifier") == "RESPONSE":
                cr = rd.find(f"{ns}correctResponse")
                if cr is not None:
                    for val in cr.findall(f"{ns}value"):
                        if val.text:
                            opt_text = option_idents.get(
                                val.text.strip(), val.text.strip()
                            )
                            correct_answers.append(opt_text)

        # True/False detection
        q_type = QuestionType.MULTIPLE_CHOICE.value
        if len(options) == 2:
            texts = {o["text"].lower() for o in options}
            if texts == {"true", "false"}:
                q_type = QuestionType.TRUE_FALSE.value

        return ParsedQuestion(
            question_text=question_text,
            question_type=q_type,
            options=options,
            correct_answers=correct_answers,
        )

    def _parse_qti21_text_entry(
        self, root: ET.Element, body: ET.Element, ns: str
    ) -> ParsedQuestion:
        """Parse a QTI 2.1 textEntryInteraction."""
        question_text = self._extract_body_text(body, ns)

        correct_answers = self._extract_correct_values(root, ns)

        return ParsedQuestion(
            question_text=question_text,
            question_type=QuestionType.SHORT_ANSWER.value,
            correct_answers=correct_answers,
        )

    def _parse_qti21_extended_text(
        self, root: ET.Element, body: ET.Element, ns: str
    ) -> ParsedQuestion:
        """Parse a QTI 2.1 extendedTextInteraction."""
        question_text = self._extract_body_text(body, ns)

        return ParsedQuestion(
            question_text=question_text,
            question_type=QuestionType.LONG_ANSWER.value,
        )

    def _parse_qti21_match(
        self, root: ET.Element, interaction: ET.Element, ns: str
    ) -> ParsedQuestion:
        """Parse a QTI 2.1 matchInteraction."""
        prompt_el = interaction.find(f"{ns}prompt")
        question_text = (
            prompt_el.text.strip() if prompt_el is not None and prompt_el.text else ""
        )

        match_sets = interaction.findall(f"{ns}simpleMatchSet")
        options: list[dict[str, Any]] = []

        source_items: list[tuple[str, str]] = []
        target_items: dict[str, str] = {}

        if len(match_sets) >= 2:
            for choice in match_sets[0].findall(f"{ns}simpleAssociableChoice"):
                ident = choice.get("identifier", "")
                text = choice.text.strip() if choice.text else ""
                source_items.append((ident, text))

            for choice in match_sets[1].findall(f"{ns}simpleAssociableChoice"):
                ident = choice.get("identifier", "")
                text = choice.text.strip() if choice.text else ""
                target_items[ident] = text

        # Build options as left/right pairs
        for _src_ident, src_text in source_items:
            options.append({"left": src_text, "right": ""})

        # Try to get correct pairings from responseDeclaration
        for rd in root.findall(f"{ns}responseDeclaration"):
            if rd.get("identifier") == "RESPONSE":
                cr = rd.find(f"{ns}correctResponse")
                if cr is not None:
                    for i, val in enumerate(cr.findall(f"{ns}value")):
                        if val.text:
                            parts = val.text.strip().split()
                            if len(parts) == 2 and i < len(options):
                                tgt_ident = parts[1]
                                options[i]["right"] = target_items.get(
                                    tgt_ident, tgt_ident
                                )

        return ParsedQuestion(
            question_text=question_text,
            question_type=QuestionType.MATCHING.value,
            options=options,
        )

    @staticmethod
    def _extract_correct_values(root: ET.Element, ns: str) -> list[str]:
        """Extract correct answer values from QTI 2.1 responseDeclaration."""
        answers: list[str] = []
        for rd in root.findall(f"{ns}responseDeclaration"):
            if rd.get("identifier") == "RESPONSE":
                cr = rd.find(f"{ns}correctResponse")
                if cr is not None:
                    answers.extend(
                        val.text.strip() for val in cr.findall(f"{ns}value") if val.text
                    )
        return answers

    @staticmethod
    def _extract_body_text(body: ET.Element, ns: str) -> str:
        """Extract text from itemBody <p> elements."""
        return " ".join(p.text.strip() for p in body.findall(f"{ns}p") if p.text)


# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------

qti_exporter = QTIExporter()
qti_importer = QTIImporter()
