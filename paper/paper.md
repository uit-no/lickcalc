---
title: 'lickcalc: Easy analysis of lick microstructure in experiments of rodent ingestive behaviour'
tags:
  - Python
  - feeding behaviour
  - neuroscience
  - hunger
  - thirst
authors:
  - name: K. Linnea Volcko
    orcid: 0000-0002-4234-0703
    affiliation: 1
  - name: James E. McCutcheon
    corresponding: true
    orcid: 0000-0002-6431-694X
    affiliation: 1
affiliations:
 - name: Dept. of Psychology, UiT The Arctic University of Norway, Tromsø, Norway
   index: 1
   ror: 00wge5k78
date: 15 October 2025
bibliography: paper.bib

---

# Summary

Lick microstructure

# Statement of need

`lickcalc` is a software suite that...

microstructural analysis first described in [@davis:1992]
used more recently to understand [@naneix:2020]

Weibull analysis as described in [@davis:1996]



# Mathematics

Single dollars ($) are required for inline mathematics e.g. $f(x) = e^{\pi/x}$

Double dollars make self-standing equations:

$$\Theta(x) = \left\{\begin{array}{l}
0\textrm{ if } x < 0\cr
1\textrm{ else}
\end{array}\right.$$

You can also use plain \LaTeX for equations
\begin{equation}\label{eq:fourier}
\hat f(\omega) = \int_{-\infty}^{\infty} f(x) e^{i\omega x} dx
\end{equation}
and refer to \autoref{eq:fourier} from text.

# Citations

Citations to entries in paper.bib should be in
[rMarkdown](http://rmarkdown.rstudio.com/authoring_bibliographies_and_citations.html)
format.

If you want to cite a software repository URL (e.g. something on GitHub without a preferred
citation) then you can do it with the example BibTeX entry below for @fidgit.

For a quick reference, the following citation commands can be used:
- `@author:2001`  ->  "Author et al. (2001)"
- `[@author:2001]` -> "(Author et al., 2001)"
- `[@author1:2001; @author2:2001]` -> "(Author1 et al., 2001; Author2 et al., 2002)"

# Figures

Figures can be included like this:
![Caption for example figure.\label{fig:example}](figure.png)
and referenced from text using \autoref{fig:example}.

Figure sizes can be customized by adding an optional second parameter:
![Caption for example figure.](figure.png){ width=20% }

# Acknowledgements

We acknowledge contributions from ...

# References