# Quasi-extinction simulation stage exclusions

There are several functionality and visual aspects for the quasi-extinction simulation that must be improven

## Stage exclusion

Some stages are sometimes irrelevant for quasi-extinction studies. These are stages where, a low amount of individuals will not lead to an extinction of the specie.

To implement this, we can have several options. I think that the most reasonable option is the following one:

At the start of a quasi-extinction analysis, we have a set A of N matrices. Those matrices must be exactly the same, so therefore, thay must have the same dimensions and therefore, the same stages.

Right now, before running a quasi-extinction analysis, we can set a threshold. This threshold means that, if any of those stages goes below that specific threshold, we consider that the specie is quasi-extinct.

We must allow the user to select some stages to exclude them for the analysis. Therefore, the population of these stages will not be considered when we need to determine the extinction of that specie.

Another important improvement will be to set an specific threshold for each of the stages. That means, for a population with stages { *a*, *b*, *c*}, we must be able to specify that the threshold for stage *a* is 200, the threshold for stage *b* is 150 and that we don't want to observ stage *c*.

This doesn't mean that we'll get rid of the global threshold, so for example for a population with stages { *a*, *b*, *c*, *d*, .... , $N$}, we can specify an specific threshold of 150 for stage *b*, exclude stage *c* and set a global threshold of 100 for the rest of the set without having to intruduce it by hand fo all the stages.

## Visualisation details

We need to give the user more information about the simulation that he's running, so we need to show the thresholds that he set and a modal with all the matrix that he selected for the simulation.