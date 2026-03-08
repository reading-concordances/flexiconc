# Introduction to FlexiConc

**FlexiConc** is a Python package developed to facilitate and enhance the computational analysis of concordances, primarily intended for use in corpus linguistic research. The package is rooted in theoretical insights from the “Reading Concordances in the 21st Century” research project supported by the Arts and Humanities Research Council (AHRC) (grant references: AH/X002047/1 & AH/X002047/2) and the Deutsche Forschungsgemeinschaft (DFG) (grant reference: 508235423).

FlexiConc systematically supports analysts in organizing, filtering, and interpreting concordance data through algorithmic assistance, making complex corpus research reproducible and accountable.

## What is FlexiConc?

FlexiConc provides computational methods to assist corpus linguists in systematically exploring concordances—lists of text segments centered around keywords or query matches (nodes). It enables flexible manipulation of concordances through a structured approach that includes selecting subsets of data, ordering concordance lines based on specific criteria, and grouping them into meaningful clusters or partitions.

## Core Features

### Concordance Views

A concordance view is a filtered, ordered, grouped, or otherwise transformed subset of a concordance, designed to help analysts identify and interpret patterns. Concordance views support "vertical reading" via traditional KWIC (Keyword in Context) format, allowing efficient examination of recurring linguistic patterns.

### Core Analytical Strategies
FlexiConc is built around three main strategies:

1. **Selecting:** Focusing on subsets of concordance lines based on criteria such as metadata categories, contextual keywords, or random sampling.
2. **Ordering:** Arranging concordance lines either through sorting (pairwise comparisons) or ranking (based on numeric preference scores to prioritize lines of interest).
3. **Grouping:** Organizing concordance lines into meaningful categories, either by partitioning based on explicit criteria or clustering by semantic, syntactic, or lexical similarity.

### Analysis Trees
The analytical workflow in FlexiConc is structured via an **analysis tree**, a hierarchical history of applied algorithms and operations. Each node in the tree represents either a subset selection or a rearrangement (ordering/grouping) of concordance lines, preserving a complete record of the analyst's exploratory steps. This ensures research transparency, facilitates reproducibility, and enables easy revisiting of previous analytical steps.

## Integration and Extensibility

FlexiConc is designed primarily as a backend library for integration into concordancer applications. The host application handles corpus queries, initial concordance generation, user interaction, and visualization, while FlexiConc processes concordances, applies algorithms, and manages analysis trees. This clear division ensures FlexiConc can be integrated into various concordancing environments easily.

FlexiConc's modular design supports adding new analytical algorithms seamlessly, fostering ongoing innovation and adaptability to evolving research needs.

### Intended Users and Use Cases
FlexiConc is suited for:

- Corpus linguists performing qualitative and quantitative pattern analyses.
- Developers of concordance applications seeking computational backend solutions.
- Educators and researchers requiring reproducible and systematic documentation of analytical steps.

### Technical Overview
FlexiConc operates on structured concordance data containing token and metadata annotations provided by the host application.

Algorithm outputs—subset selections, sorting keys, clustering information—are returned as structured concordance views, enabling host applications to provide clear visual representations.

### Documentation

The [documentation](https://fau-klue.github.io/flexiconc-docs/) is available. However, it is still in development and the details of the API are subject to change.