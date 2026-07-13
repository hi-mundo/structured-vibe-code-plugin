# Methodology and Published Foundations

Use these sources as methodological anchors, not as claims that every repository requires formal methods.

## Verification and validation

- IEEE 1012 defines verification and validation processes for systems, software, and hardware. Use its distinction operationally: verification asks whether the work product satisfies specified requirements; validation asks whether the resulting system fulfills intended use. Publisher: IEEE. https://standards.ieee.org/ieee/1012/7177/
- IEEE 29119 provides a family of software testing standards covering concepts, processes, documentation, and techniques. Use it to keep evidence, procedure, expected result, and actual result distinct. Publisher: IEEE. https://standards.ieee.org/ieee/29119-1/8297/

## Model-based and specification-oriented testing

- Utting, Pretschner, and Legeard, “A taxonomy of model-based testing approaches,” *Software Testing, Verification and Reliability*, 22(5), 297–312, 2012. DOI: 10.1002/stvr.456. It supports deriving tests from explicit models of the system or environment. Publisher: Wiley. https://doi.org/10.1002/stvr.456
- Hierons et al., “Using formal specifications to support testing,” *ACM Computing Surveys*, 41(2), 2009. DOI: 10.1145/1459352.1459354. It surveys how specifications support test generation and evaluation. Publisher: ACM. https://doi.org/10.1145/1459352.1459354
- Miller and Strooper, “A case study in model-based testing of specifications and implementations,” *Software Testing, Verification and Reliability*, 22(1), 33–63, 2012. DOI: 10.1002/stvr.431. It examines the relationship between testing specifications and implementations. Publisher: Wiley. https://doi.org/10.1002/stvr.431

## Defect semantics and classification

- Chillarege et al., “Orthogonal Defect Classification—A Concept for In-Process Measurements,” *IEEE Transactions on Software Engineering*, 18(11), 943–956, 1992. DOI: 10.1109/32.177364. ODC uses semantic defect attributes such as type and trigger to produce process feedback. Publisher: IEEE; author copy indexed by IBM Research. https://doi.org/10.1109/32.177364
- Butcher, Munro, and Kratschmer, “Improving software testing via ODC: Three case studies,” *IBM Systems Journal*, 41(1), 2002. DOI: 10.1147/sj.411.0031. It demonstrates using defect profiles to redirect testing toward product risks. Publisher: IBM. https://doi.org/10.1147/sj.411.0031

## Repository history and causal caution

- Śliwerski, Zimmermann, and Zeller, “When Do Changes Induce Fixes?”, *Mining Software Repositories*, 2005. The SZZ approach links bug-fixing changes to candidate introducing changes through version history. Publisher: ACM workshop proceedings. https://www.st.cs.uni-saarland.de/papers/msr2005/
- Borg et al., “SZZ Unleashed: An Open Implementation of the SZZ Algorithm,” 2019. It documents a reproducible Git implementation and explicitly frames SZZ as heuristic. https://arxiv.org/abs/1903.01742
- Rodríguez-Pérez et al., “A Framework for Evaluating the Results of the SZZ Approach for Identifying Bug-Introducing Changes,” *IEEE Transactions on Software Engineering*, 43(7), 641–657, 2017. DOI: 10.1109/TSE.2016.2616306. It evaluates threats to the accuracy of SZZ results. Publisher: IEEE. https://doi.org/10.1109/TSE.2016.2616306
- Herbold et al., “Problems with SZZ and Features,” *Empirical Software Engineering*, 27, 2022. DOI: 10.1007/s10664-021-10092-4. It documents data-collection and labeling limitations relevant to causal claims from history. Publisher: Springer Nature. https://doi.org/10.1007/s10664-021-10092-4

## Translation into this skill

- Build a behavioral model before selecting evidence.
- Compare specification/intended use with implementation, not implementation with itself.
- Classify defects by the semantic mismatch and its trigger.
- Use history to explain evolution and generate hypotheses.
- Require direct evidence before upgrading a historical hypothesis to a causal conclusion.
