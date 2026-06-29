// chapters/01_description/index.typ
#import "../../template.typ": guia

= General Description of the Project <sec:general-description>

== Summary

This project is a web application developed in collaboration with the Faculty of
Biology, designed to simulate population growth dynamics for educational purposes. Its
main goal is to serve as an interactive teaching tool that helps university students
and researchers or professors better understand and visualize how populations evolve
over time.

The application is entirely web-based, meaning it requires no installation and can be
accessed from any device with a browser and an internet connection. It is intended to
be free and openly available to anyone in the world, with no barriers to access. This
global accessibility is a core design principle of the project, as the aim is to bring
quality educational resources to as wide an audience as possible, regardless of their
institution or geographic location.

The project was born out of a real collaboration between the School of Engineering and
the Faculty of Biology, which gives it a genuine interdisciplinary and practical
context. Although the application is currently functional and actively under
development, the intention is for it to eventually be deployed and used in real
academic settings, both as a complement to biology courses and as a resource for
independent study and research.

By combining an intuitive interface with solid scientific foundations, the application
bridges the gap between theoretical population ecology and hands-on learning, making
abstract mathematical models tangible and interactive for its users.

== Keywords

Population dynamics, Educational simulation, Web application, Computational biology,
Interactive visualization

== Abstract

This project presents the design and development of a web application created in
collaboration with the Faculty of Biology, aimed at simulating population growth
dynamics for educational purposes. The tool allows users to interactively explore
stage-structured matrix population models (Lefkovitch and Leslie matrices) sourced
from the COMPADRE and COMADRE databases, through intuitive visual representations
that make abstract demographic concepts more accessible and engaging.

The application is entirely browser-based, requiring no installation, and is freely
available to anyone with an internet connection. It targets university students,
researchers, and professors as its primary audience, serving as a complementary
resource for teaching and studying population ecology.

The project emerges from a genuine interdisciplinary collaboration between the fields
of software engineering and biology, with the long-term goal of deploying the tool in
real academic environments worldwide. The current version is functional and under
active development, with a focus on usability, scientific accuracy, and universal
accessibility.

== Biological Context

This section provides an overview of the biological context in which the project is situated. It explains how the application defines the concepts of *simulation* and *quasi-extinction* in the context of population dynamics.

=== Data Background

The concept of *population model* refers to a mathematical representation of how likely a population is to change over time, based on field data collected from real populations.

A population itself has several stages, depending on the species; these stages may include: eggs, larvae, juveniles, adults, and senescent individuals. As we standardize the population to a set of $M$ stages, we can represent a specific population as a vector $P(t) = (p_1(t), p_2(t), ..., p_M(t))$, where $p_i(t)$ is the number of individuals in stage $i$ at time $t$.

Therefore, if we want to model the population dynamics of a specific species, we need to define the transition probabilities between stages, which can be represented as an $M times M$ matrix $A$, where each element $a_{i,j}$ represents the probability of an individual in stage $j$ transitioning to stage $i$ in the next time step. This kind of stage-structured projection matrix is known in the literature as a *Lefkovitch matrix* (a generalization of the classic age-structured *Leslie matrix*, which restricts transitions to a fecundity row and a survival sub-diagonal) @caswell2001. The COMPADRE matrices used in this project are Lefkovitch (or, where strictly age-structured, Leslie) matrices.

=== Simulation Analysis

In the context of this project, a *simulation* refers to the process of using a mathematical model to predict the future state of a population based on its current state and the defined transition probabilities. We can use the population vector $P(t)$ and the transition matrix $A$ to project the population into the future using the equation: $P(t+1) = A * P(t)$

This equation allows us to create the projection of a matrix $A$ with an initial population vector $P(0)$, which represents the population at time $t=0$. By iteratively applying the transition matrix $A$ to the population vector, we can project how the population evolves over time. 

This is known as a *population projection*, and in the application we'll refer to it as a *deterministic simulation*.


==== Introducing Stochasticity

The fact is that, in real life, populations are subject to random events and environmental fluctuations that can affect their growth and survival. Therefore, we also consider *stochastic simulations*, which incorporate randomness into the population projection process. The way we achieve stochastic simulations is the following one:

Instead of having a unique matrix $A$, we must start the simulation with a set of 2 to $N$ matrices $A$ of the same species, that might have been registered under different environmental conditions (ex. different seasons). We also need again the vector $P(0)$ as starting point.

The next step is defining the value of $R$, the total number of *iterations* (runs) to perform. On each iteration, a matrix at random is picked from the set of matrices and used for the entire projection - that is, the same matrix is applied at every step of that iteration, from $P(0)$ through $P(n)$. We continue until all $R$ iterations have been run. In this process, we keep track of the frequency with which each matrix is used in a vector $F$ of size $N$, where $f_1$ represents how many times the first matrix in the set has been picked. Then, with the results of all iterations, we compute the mean, minimum and maximum values and standard deviation for each stage at each $t$ step, across iterations.

From these simulations we can also obtain other relevant information, such as the frequency-weighted mean transition matrix $overline(A) = 1/R sum_(k=1)^R A_k$ (equivalently, $overline(A) = sum_(j=1)^N (f_j / R) A_j$ using the frequency vector $F$). Note that, because repeated matrix multiplication is non-linear, projecting $overline(A)$ alone does *not* reproduce the exact same trajectory as the stochastic run - exact reproducibility of a given run is instead achieved by storing the random seed used to pick the matrices at each iteration.

// #block(
//   stroke: 0.5pt + luma(200), radius: 3pt, inset: 10pt, width: 100%,
// )[
//   *Note:* There are more biologically realistic ways of modelling stochasticity, such
//   as drawing the entries of the transition matrix $A$ from a probability distribution
//   at each time step (rather than switching between a fixed, pre-registered set of
//   matrices). However, this approach will not be implemented in the application.
// ]

=== Quasi-extinction analysis

Once we have our stochastic simulations defined, we introduce the concept of *quasi-extinction* analysis. The quasi-extinction analysis consists in studying how likely a population is to become extinct. In the book "Quantitative conservation biology : theory and practice of population viability analysis" @quantitative-conservation-biology, it's defined as: "the population falling below a quasi-extinction threshold set as the minimum number of individuals (or, often, females) below which the population is likely to be critically and immediately imperiled"

To perform a *quasi-extinction analysis*, we need the same things as for a stochastic simulation (there's no point in performing an analysis of this nature over a single deterministic projection, as we would always obtain either a 100% or a 0% probability). Then, we define a threshold vector of size $M$, with one entry per population stage. This vector tells us the minimum amount of individuals in that specific stage required to consider the species *quasi-extinct*. This means that, if in a projection the amount of individuals in a specific stage goes below that threshold at any step, we consider that iteration to have hit quasi-extinction.

Finally, we obtain the probability of *quasi-extinction* as the proportion of iterations that hit quasi-extinction out of the $R$ total iterations performed:
$ P_"qe" = n_"extinct" / R $

We can also obtain more relevant information from this kind of simulations, like which stage is more likely to trigger *quasi-extinction*, at which step... .

The R implementations of these methods provided by the github repository *eco3r* @eco3r of Mario Quevedo de Anta served as a methodological reference for the algorithms implemented in this project.

#pagebreak(weak: true)