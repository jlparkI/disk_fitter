import numpy as np


class mgm():

  def __init__(self):
    self.cutoff_R = 0
    self.cutoff_S = 0

  def gini(self, population):
    prob_2 = (np.argwhere(population==2).shape[0] / population.shape[0])**2
    prob_1 = (np.argwhere(population==1).shape[0] / population.shape[0])**2
    prob_0 = (np.argwhere(population==0).shape[0] / population.shape[0])**2
    return (1 - prob_2 - prob_1 - prob_0)

  def fit_disk_data(self, input_x, input_y):
    allowed_widths = [1.0, 2.0, 3.0, 4.0]
    best_score_so_far = np.ones((4))
    best_cutoffs_so_far = np.zeros((4,2))
    for i, width in enumerate(allowed_widths):
      proposed_cutoff_R = np.min(input_x)
      proposed_cutoff_S = proposed_cutoff_R + width
      while (proposed_cutoff_R) <= np.max(input_x):
        current_score = self.score_disk_fit(input_x, input_y, proposed_cutoff_S,
                                       proposed_cutoff_R)
        if current_score <= best_score_so_far[i]:
          best_score_so_far[i] = current_score
          best_cutoffs_so_far[i,0] = proposed_cutoff_R
          best_cutoffs_so_far[i,1] = proposed_cutoff_S
        proposed_cutoff_R += 1
        proposed_cutoff_S += 1
    single_best_score = np.min(best_score_so_far)
    best_result_index = np.argmin(best_score_so_far)
    self.cutoff_R = best_cutoffs_so_far[best_result_index,0]
    self.cutoff_S = best_cutoffs_so_far[best_result_index,1]
    if np.argwhere(best_score_so_far == single_best_score).shape[0] > 1:
      return [str(allowed_widths[i]) for i in range(0,4) if 
              best_score_so_far[i] == single_best_score]
    else:
      return []
    
        

  def score_disk_fit(self, input_x, input_y, proposed_cutoff_S,
                proposed_cutoff_R):
    category_indices = [np.argwhere(input_x>=proposed_cutoff_S).flatten()]
    category_indices.append(np.argwhere(input_x<=proposed_cutoff_R).flatten())
    category_indices.append(np.asarray([i for i in range(0, input_x.shape[0]) if input_x[i] <
                             proposed_cutoff_S and input_x[i] > proposed_cutoff_R]))
    base_score = 0
    for category_index in category_indices:
      if category_index.shape[0] > 0:
        base_score += (category_index.shape[0] / input_x.shape[0]) * self.gini(input_y[category_index])
    return base_score
