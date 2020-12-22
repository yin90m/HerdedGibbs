import numpy as np


def herded_gibbs_assign(likelihood, n_samples=1000, burnin=0):
    """
    Approximates LMB weights by using assignments generated by herded Gibbs Sampling

    Parameters
    ----------
    likelihood:     LMB likelihood
    n_samples:      no. of samples to draw
    burnin:         no. of samples to ignore at the beginning

    Returns         approximated LMB weights
    -------

    """
    likelihood = np.maximum(likelihood, 1e-6)
    r = likelihood.shape[0]
    c = likelihood.shape[1]
    lmb_weights = np.zeros((r, c), dtype=np.float64)

    # define cyclic assignment and assign to non-blocking column
    assignment = np.ones(r, dtype=np.int64)

    # blocked measurements cannot be assigned
    blocked = np.zeros(c, dtype=np.int64)

    # herded gibbs weight vectors
    hg_weights = dict()

    tt_range = np.arange(r)  # indices of targets
    gibbs_costs = np.zeros(n_samples, dtype=np.float64)  # costs of gibbs assignments
    sol_id = 0
    for q in range(n_samples + burnin):
        gibbs_costs[sol_id] = 1.0
        # inner iteration over rows
        for i in range(r):
            # lift assignment for current sample and last column (non-blocking)
            blocked[assignment[i]] = 0
            blocked[0] = 0  # first two columns are not blocking
            blocked[1] = 0

            idx = (i,) + tuple(assignment[tt_range != i])
            try:
                w, cond_prob = hg_weights.get(idx)
            except (KeyError, TypeError):
                cond_prob = (likelihood[i] * (1 - blocked)) / np.sum(
                    likelihood[i] * (1 - blocked))
                w = cond_prob

            # sample
            assignment[i] = np.argmax(w)

            # update weight vector
            w = w + cond_prob  # likelihood in blocked column is 0
            w[assignment[i]] -= 1

            hg_weights[idx] = (w, cond_prob)

            blocked[assignment[i]] = 1  # block measurement

            if q >= burnin:
                # update cost for current cycle
                gibbs_costs[sol_id] *= likelihood[i, assignment[i]]

        if q < burnin:  # don't save assignment
            continue

        print(assignment - 1)

        # compare to existing solutions
        duplicate_found = False
        for s in range(sol_id):
            if gibbs_costs[sol_id] == gibbs_costs[s]:
                duplicate_found = True
                break
        if not duplicate_found:
            lmb_weights[tt_range, assignment] += gibbs_costs[sol_id]

            # go to next cycle
            sol_id += 1
    norm = np.sum(gibbs_costs[:sol_id])
    lmb_weights /= norm
    return lmb_weights
