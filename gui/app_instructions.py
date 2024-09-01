# app instructions, in html for rich text formatting

INSTRUCTIONS_TEXT = """
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; }
        h1 { font-size: 18px; font-weight: bold; text-align: center; }
        p { margin: 8px 0; }
        ul { margin: 8px 0 16px 20px; }
        .subsection { margin-left: 20px; font-style: italic; }
        .subsection ul { margin-left: 20px; }
    </style>
</head>
<body>
    <h1>Job Matching Tool - Instructions</h1>

    <h2>Important Notes:</h2>
    <ul>
        <li>This matching is <strong>instructor-agnostic</strong>. Matches are based on <strong>preferences only, NOT qualifications.</strong></li>
        <li>Therefore, it's important to view these results as a starting point rather than a final solution.</li>
        <li>Instructor order in the CSV influences results. The most important or senior instructors should be first.</li>
    </ul>

    <h2>Matching Strategies:</h2>
    <ul>
        <li><strong>Bipartite Matching:</strong> Maximizes matched pairs, weighted by preference and seniority.</li>
        <li><strong>Stable Marriage:</strong> Ensures mutually agreeable matches.</li>
        <li><strong>Linear Programming:</strong> Optimizes overall satisfaction (not individual satisfaction).</li>
        <li>Early testing suggests bipartite matching or stable marriage seem to perform better.</li>
    </ul>

    <h2>Required Inputs for Drag and Drop:</h2>
    <div class="subsection">
        <h3>Courses CSV (or xls):</h3>
        <ul>
            <li><strong>Course Name:</strong> e.g., "PS211"</li>
            <li><strong>Course ID:</strong> The course number, e.g., "211"</li>
            <li><strong>Sections Available:</strong> Integer count of sections available</li>
        </ul>

        <h3>Instructors CSV (or xls):</h3>
        <ul>
            <li><strong>Instructor Name:</strong> Self-explanatory</li>
            <li><strong>Degree:</strong> "mas" or "phd"</li>
            <li><strong>Max Classes:</strong> Integer count of total sections available to teach</li>
            <li><strong>Preference_1, Preference_2, ...:</strong> Each preference should be contained in the "course name" column of the Courses CSV</li>
        </ul>
    </div>

    <h2>Operating Instructions:</h2>
    <ul>
        <li>Load Instructor File.</li>
        <li>Load Course File.</li>
        <li>Select Matching Algorithm.</li>
        <li>Run Matching.</li>
        <li>Print/Export Results.</li>
    </ul>
</body>
</html>
"""
