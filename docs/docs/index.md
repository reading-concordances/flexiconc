# FlexiConc

This guide provides a comprehensive overview of FlexiConc, a Python package to streamline and enhance the computational analysis of concordances in corpus linguistic research.

---

## Introduction

**FlexiConc** is a Python package developed to support corpus linguists by automating and simplifying the analysis of concordances—lists of text segments centered around keywords or query matches. The package is informed by theoretical insights from the “Reading Concordances in the 21st Century” research project, supported by the Arts and Humanities Research Council (AHRC, grant reference: AH/X002047/1) and the Deutsche Forschungsgemeinschaft (DFG, grant reference: 508235423).

FlexiConc is built to facilitate a reproducible and accountable workflow in corpus research by systematically organizing, filtering, and interpreting concordance data.

---

## What is FlexiConc?

FlexiConc provides a suite of computational methods to flexibly manipulate concordance data, facilitating detailed pattern recognition and analysis.

---

## Core Features

### Concordance Views

FlexiConc allows the creation of **concordance views**, which are tailored representations of the subsets of the overall concordance.

### Core Analytical Strategies

FlexiConc is built around three fundamental strategies:

1. **Selecting**  
   Focus on specific subsets of concordance lines based on a variety of criteria, including metadata categories and contextual keywords.

2. **Ordering**  
   Arrange concordance lines by sorting or ranking them, using numeric preference scores to prioritize those of interest.

3. **Grouping**  
   Organize lines into meaningful clusters by applying explicit partitioning criteria or through clustering based on similarity measures.

### Analysis Trees

A crucial feature of FlexiConc is its **analysis tree** structure. Each node in this tree represents an operation (either a selection or a rearrangement) applied to the concordance data. This hierarchical record provides:

- **Transparency**: A complete history of the analytical steps performed.
- **Reproducibility**: Easy revisitation and validation of the analysis process.
- **Documentation**: A structured log that aids both in understanding and communicating the research methodology.

---

## Integration and Extensibility

FlexiConc is designed as a backend library to be seamlessly integrated into various concordancer applications. Its architecture enables:

- **Seamless Integration**: The host application manages corpus queries, initial concordance generation, and user interaction, while FlexiConc focuses on data processing and algorithmic analysis.
- **Modular Design**: New analytical algorithms can be added with minimal effort, ensuring the package remains adaptable to evolving research needs.

### Intended Users and Use Cases

FlexiConc is ideally suited for:

- **Corpus Linguists**: Those conducting both qualitative and quantitative analyses of linguistic patterns.
- **Application Developers**: Developers seeking robust backend solutions for concordance applications.
- **Educators and Researchers**: Individuals requiring systematic and reproducible documentation of their analytical workflows.

---

To the users of FlexiConc, we recommend exploring the sections listed under **Flexiconc for Users** in the navigation menu as well as the **Algorithms** section for detailed information on the available selecting, ordering, and grouping algorithms.