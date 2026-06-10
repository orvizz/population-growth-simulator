#import "../../../template.typ": user-story

#user-story(
  role:     [registered user],
  want:     [start a quasi-extinction analysis on a stochastic population scenario],
  benefit:  [estimate the probability that the population falls below a critical abundance threshold within a given time horizon],
  priority: "Must",
  points:   [8],
  criteria: (
    [I can submit a quasi-extinction job by selecting the matrices, initial vector, extinction threshold, and time horizon.],
    [The job runs asynchronously; I receive an immediate acknowledgement (HTTP 202) and can continue using the application.],
    [I can poll the job status and view a progress indicator while it is running.],
    [On completion, a probability-over-time curve is rendered showing the cumulative quasi-extinction probability.],
  ),
)
