# FlexiConc for developers

FlexiConc is intended for developers who want to integrate advanced concordance analysis capabilities into their corpus management systems. The package is designed to be modular and extensible, allowing developers to add new features and algorithms as needed.

The host app can pass a concordance to FlexiConc, which will then process the data and return the results. This allows for a clear separation of concerns, where the host app handles user interaction and corpus management, while FlexiConc focuses on the analytical tasks. FlexiConc also takes care of the analysis tree, which records all operations performed on the concordance data, ensuring transparency and reproducibility.