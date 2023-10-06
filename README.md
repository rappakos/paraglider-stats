# paraglider-stats
Tool to download paraglider flights (eg from xcontest) and evaluate them


## Data 

Flights scraped from [xcontest 2023 PG sport ranking](https://www.xcontest.org/2023/world/en/ranking-pg-sport/).
Out of the ~24K pilots there, roughly the first 10k (therefore ca 60k) are taken into account.


## Theory

Statement: The XC points for a given glider type follow [log-normal](https://en.wikipedia.org/wiki/Log-normal_distribution)

This means that once the parameters mu and sigma are estimated, we can compute the probability of achieving a given number of XC points with the given glider.

## Results

This year has been quite exciting since a bunch of new EN-C 2-liners appeared on the market.