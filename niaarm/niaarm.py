from niaarm.rule import Rule
from niaarm.feature import Feature
from niapy.problems import Problem
import numpy as np
import csv


class NiaARM(Problem):
    r"""Association Rule Mining as an optimization problem.

    The implementation is composed of ideas found in the following papers:

    * I. Fister Jr., A. Iglesias, A. Gálvez, J. Del Ser, E. Osaba, I Fister.
      [Differential evolution for association rule mining using categorical and numerical attributes]
      (http://www.iztok-jr-fister.eu/static/publications/231.pdf)
      In: Intelligent data engineering and automated learning - IDEAL 2018, pp. 79-88, 2018.

    * I. Fister Jr., V. Podgorelec, I. Fister.
      Improved Nature-Inspired Algorithms for Numeric Association Rule Mining.
      In: Vasant P., Zelinka I., Weber GW. (eds) Intelligent Computing and Optimization. ICO 2020.
      Advances in Intelligent Systems and Computing, vol 1324. Springer, Cham.

    Args:
        dimension (int): Dimension of the optimization problem for the dataset.
        features (list[Feature]): List of the dataset's features.
        transactions (pandas.Dataframe): The dataset's transactions.
        metrics (Union[Dict[str, float], Sequence[str]]): Metrics to take into account when computing the fitness.
         Metrics can either be passed as a Dict of {'metric_name': <weight of metric (in range [0, 1])>} or
         a Sequence (list or tuple) of metrics as strings. In the latter case, the weights of the metrics will be
         set to 1.
        logging (bool): If ``logging=True``, fitness improvements are printed. Default: ``False``.

    Attributes:
        rules (list[Rule]): List of mined association rules.

    """

    available_metrics = (
        'support', 'confidence', 'coverage', 'interest', 'comprehensibility', 'amplitude', 'inclusion', 'rhs_support'
    )

    def __init__(self, dimension, features, transactions, metrics, logging=False):
        self.features = features
        self.transactions = transactions

        if not metrics:
            raise ValueError('No metrics provided')

        if isinstance(metrics, dict):
            self.metrics = tuple(metrics.keys())
            self.weights = np.array(tuple(metrics.values()))
        elif isinstance(metrics, (list, tuple)):
            self.metrics = tuple(metrics)
            self.weights = np.ones(len(self.metrics))
        else:
            raise ValueError('Invalid type for metrics')

        if not set(self.metrics).issubset(self.available_metrics):
            invalid = ', '.join(set(self.metrics).difference(self.available_metrics))
            raise ValueError(f'Invalid metric(s): {invalid}')

        self.sum_weights = np.sum(self.weights)

        self.logging = logging
        self.best_fitness = np.NINF
        self.rules = []
        super().__init__(dimension, 0.0, 1.0)

    def export_rules(self, path):
        r"""Export mined association rules to a csv file.

        Args:
            path (str): Path.

        """
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)

            # write header
            writer.writerow(("antecedent", "consequent", "fitness") + self.available_metrics)

            for rule in self.rules:
                writer.writerow(
                    [rule.antecedent, rule.consequent, rule.fitness] + [getattr(rule, metric) for metric in
                                                                        self.available_metrics])
        print(f"Rules exported to {path}")

    def sort_rules(self, by='fitness', reverse=True):
        """Sort mined association rules by fitness.

        Args:
            by (Optional[str]): Attribute to sort rules by. Default: ``'fitness'``.
            reverse (Optional[bool]): Sort in reverse order. Default: ``True``.

        """
        self.rules.sort(key=lambda x: getattr(x, by), reverse=reverse)

    def build_rule(self, vector):
        rule = []

        permutation = vector[-len(self.features):]
        permutation = sorted(range(len(permutation)), key=lambda k: permutation[k])

        for i in range(len(self.features)):
            current_feature = permutation[i]
            feature = self.features[current_feature]

            # set current position in the vector
            vector_position = self.feature_position(current_feature)

            # get a threshold for each feature
            threshold_position = vector_position + self.threshold_move(current_feature)
            if vector[vector_position] > vector[threshold_position]:
                if feature.dtype == 'float':
                    border1 = vector[vector_position] * (feature.max_val - feature.min_val) + feature.min_val
                    vector_position = vector_position + 1
                    border2 = vector[vector_position] * (feature.max_val - feature.min_val) + feature.min_val

                    if border1 > border2:
                        border1, border2 = border2, border1
                    rule.append(Feature(feature.name, feature.dtype, border1, border2))

                elif feature.dtype == 'int':
                    border1 = round(vector[vector_position] * (feature.max_val - feature.min_val) + feature.min_val)
                    vector_position = vector_position + 1
                    border2 = round(vector[vector_position] * (feature.max_val - feature.min_val) + feature.min_val)

                    if border1 > border2:
                        border1, border2 = border2, border1
                    rule.append(Feature(feature.name, feature.dtype, border1, border2))
                else:
                    categories = feature.categories
                    selected = round(vector[vector_position] * (len(categories) - 1))
                    rule.append(Feature(feature.name, feature.dtype, categories=[feature.categories[selected]]))
            else:
                rule.append(None)
        return rule

    def threshold_move(self, current_feature):
        if self.features[current_feature].dtype == "float" or self.features[current_feature].dtype == "int":
            move = 2
        else:
            move = 1
        return move

    def feature_position(self, feature):
        position = 0
        for i in range(feature):
            if self.features[i].dtype == "float" or self.features[i].dtype == "int":
                position = position + 3
            else:
                position = position + 2
        return position

    def _evaluate(self, sol):
        r"""Evaluate association rule."""
        cut_value = sol[self.dimension - 1]  # get cut point value
        solution = sol[:-1]  # remove cut point

        cut = _cut_point(cut_value, len(self.features))

        rule = self.build_rule(solution)

        # get antecedent and consequent of rule
        antecedent = rule[:cut]
        consequent = rule[cut:]

        antecedent = [attribute for attribute in antecedent if attribute]
        consequent = [attribute for attribute in consequent if attribute]

        # check if the rule is feasible
        if antecedent and consequent:
            rule = Rule(antecedent, consequent, transactions=self.transactions)
            metrics = [getattr(rule, metric) for metric in self.metrics]
            fitness = np.dot(self.weights, metrics) / self.sum_weights
            rule.fitness = fitness

            if rule.support > 0.0 and rule.confidence > 0.0:
                # save feasible rule
                if rule not in self.rules:
                    self.rules.append(rule)

                if self.logging and fitness > self.best_fitness:
                    self.best_fitness = fitness
                    print(f'Fitness: {rule.fitness}, ' + ', '.join(
                        [f'{metric.capitalize()}: {getattr(rule, metric)}' for metric in self.metrics]))
            return fitness
        else:
            return -1.0


def _cut_point(sol, num_attr):
    cut = int(sol * num_attr)
    if cut == 0:
        cut = 1
    if cut > num_attr - 1:
        cut = num_attr - 2
    return cut
