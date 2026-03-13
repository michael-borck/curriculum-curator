#!/usr/bin/env bash
# Creates synthetic IMSCC and SCORM test fixtures for E2E tests.
# Run once: cd e2e/fixtures && bash create-fixtures.sh

set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"

# ─── Synthetic IMSCC (IMS Common Cartridge 1.1) ──────────────────────────────
echo "Creating sample-course.imscc ..."
IMSCC_DIR=$(mktemp -d)

# imsmanifest.xml — CC 1.1 with 2 web content resources across 2 weeks
cat > "$IMSCC_DIR/imsmanifest.xml" << 'MANIFEST'
<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="sample-course-manifest"
          xmlns="http://www.imsglobal.org/xsd/imscp_v1p1"
          xmlns:lom="http://ltsc.ieee.org/xsd/imscc/LOM">
  <metadata>
    <schema>IMS Common Cartridge</schema>
    <schemaversion>1.1.0</schemaversion>
    <lom:lom>
      <lom:general>
        <lom:title><lom:string>Introduction to Web Technologies</lom:string></lom:title>
      </lom:general>
    </lom:lom>
  </metadata>
  <organizations>
    <organization identifier="org1" structure="rooted-hierarchy">
      <item identifier="week01" identifierref="">
        <title>Week 1 - HTML Fundamentals</title>
        <item identifier="item01" identifierref="res01">
          <title>Lecture: HTML Basics</title>
        </item>
        <item identifier="item02" identifierref="res02">
          <title>Reading: HTML Reference</title>
        </item>
      </item>
      <item identifier="week02" identifierref="">
        <title>Week 2 - CSS Styling</title>
        <item identifier="item03" identifierref="res03">
          <title>Lecture: CSS Introduction</title>
        </item>
        <item identifier="item04" identifierref="res04">
          <title>Quiz: HTML Fundamentals</title>
        </item>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="res01" type="webcontent" href="week01/lecture_html_basics.html">
      <file href="week01/lecture_html_basics.html"/>
    </resource>
    <resource identifier="res02" type="webcontent" href="week01/reading_html_reference.html">
      <file href="week01/reading_html_reference.html"/>
    </resource>
    <resource identifier="res03" type="webcontent" href="week02/lecture_css_intro.html">
      <file href="week02/lecture_css_intro.html"/>
    </resource>
    <resource identifier="res04" type="imsqti_xmlv1p2/imscc_xmlv1p1/assessment" href="week02/quiz_html.xml">
      <file href="week02/quiz_html.xml"/>
    </resource>
  </resources>
</manifest>
MANIFEST

# Content files
mkdir -p "$IMSCC_DIR/week01" "$IMSCC_DIR/week02"

cat > "$IMSCC_DIR/week01/lecture_html_basics.html" << 'HTML'
<!DOCTYPE html>
<html><head><title>HTML Basics</title></head>
<body>
<h1>Introduction to HTML</h1>
<p>HTML (HyperText Markup Language) is the standard language for creating web pages.</p>
<h2>Key Concepts</h2>
<ul>
  <li>Elements and tags</li>
  <li>Attributes</li>
  <li>Document structure</li>
</ul>
</body></html>
HTML

cat > "$IMSCC_DIR/week01/reading_html_reference.html" << 'HTML'
<!DOCTYPE html>
<html><head><title>HTML Reference</title></head>
<body>
<h1>HTML Element Reference</h1>
<p>A comprehensive reference guide for HTML5 elements.</p>
<table>
  <tr><th>Element</th><th>Description</th></tr>
  <tr><td>&lt;div&gt;</td><td>Division or section</td></tr>
  <tr><td>&lt;span&gt;</td><td>Inline container</td></tr>
  <tr><td>&lt;p&gt;</td><td>Paragraph</td></tr>
</table>
</body></html>
HTML

cat > "$IMSCC_DIR/week02/lecture_css_intro.html" << 'HTML'
<!DOCTYPE html>
<html><head><title>CSS Introduction</title></head>
<body>
<h1>Introduction to CSS</h1>
<p>CSS (Cascading Style Sheets) controls the visual presentation of HTML documents.</p>
<h2>Selectors</h2>
<p>CSS selectors target HTML elements for styling.</p>
</body></html>
HTML

cat > "$IMSCC_DIR/week02/quiz_html.xml" << 'QTI'
<?xml version="1.0" encoding="UTF-8"?>
<questestinterop>
  <assessment title="HTML Fundamentals Quiz">
    <section>
      <item title="Question 1">
        <presentation>
          <material><mattext>What does HTML stand for?</mattext></material>
          <response_lid ident="resp1" rcardinality="Single">
            <render_choice>
              <response_label ident="A"><material><mattext>HyperText Markup Language</mattext></material></response_label>
              <response_label ident="B"><material><mattext>High Tech Modern Language</mattext></material></response_label>
            </render_choice>
          </response_lid>
        </presentation>
      </item>
    </section>
  </assessment>
</questestinterop>
QTI

# Package as .imscc (which is just a ZIP)
(cd "$IMSCC_DIR" && zip -r "$DIR/sample-course.imscc" . -x ".*")
rm -rf "$IMSCC_DIR"
echo "  Created sample-course.imscc ($(du -h "$DIR/sample-course.imscc" | cut -f1))"

# ─── Synthetic SCORM 1.2 Package ─────────────────────────────────────────────
echo "Creating sample-scorm.zip ..."
SCORM_DIR=$(mktemp -d)

# imsmanifest.xml — SCORM 1.2
cat > "$SCORM_DIR/imsmanifest.xml" << 'MANIFEST'
<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="scorm-sample"
          xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2"
          xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2">
  <metadata>
    <schema>ADL SCORM</schema>
    <schemaversion>1.2</schemaversion>
  </metadata>
  <organizations default="org1">
    <organization identifier="org1">
      <title>Data Analysis Fundamentals</title>
      <item identifier="item1" identifierref="res1" isvisible="true">
        <title>Module 1: Introduction to Data</title>
        <adlcp:prerequisites type="aicc_script"></adlcp:prerequisites>
      </item>
      <item identifier="item2" identifierref="res2" isvisible="true">
        <title>Module 2: Data Visualization</title>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="res1" type="webcontent" adlcp:scormtype="sco" href="module1/index.html">
      <file href="module1/index.html"/>
    </resource>
    <resource identifier="res2" type="webcontent" adlcp:scormtype="sco" href="module2/index.html">
      <file href="module2/index.html"/>
    </resource>
  </resources>
</manifest>
MANIFEST

mkdir -p "$SCORM_DIR/module1" "$SCORM_DIR/module2"

cat > "$SCORM_DIR/module1/index.html" << 'HTML'
<!DOCTYPE html>
<html><head><title>Introduction to Data</title></head>
<body>
<h1>Module 1: Introduction to Data</h1>
<p>Data analysis is the process of inspecting, cleansing, and modelling data.</p>
</body></html>
HTML

cat > "$SCORM_DIR/module2/index.html" << 'HTML'
<!DOCTYPE html>
<html><head><title>Data Visualization</title></head>
<body>
<h1>Module 2: Data Visualization</h1>
<p>Data visualization uses charts, graphs, and maps to communicate data insights.</p>
</body></html>
HTML

(cd "$SCORM_DIR" && zip -r "$DIR/sample-scorm.zip" . -x ".*")
rm -rf "$SCORM_DIR"
echo "  Created sample-scorm.zip ($(du -h "$DIR/sample-scorm.zip" | cut -f1))"

echo "Done. Fixtures ready in $DIR"
