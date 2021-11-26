from unittest import TestCase
from niaarm.association_rule import AssociationRule
from niaarm.dataset import Dataset


class TestSupportConfidence(TestCase):
    # let's borrow test case from wikipedia: https://en.wikipedia.org/wiki/Lift_(data_mining)
    def test_numerical_categorical(self):
        data = Dataset("datasets/wiki_test_case.csv")

        features = data.get_features()

        transactions = data.transaction_data

        antecedent_a = [['A']]

        consequence_a = [[0, 0]]

        # TODO: manual checks should be done!
        support_a = 0.42857142857142855

        confidence_a = 0.75

        vector = [0.83393188, 0.66680227, 0.67480834, 0.13308981, 0.55182048, 0.04805541, 0.51910747]

        oper = AssociationRule(features)

        cut = oper.get_cut_point(0, len(features))

        rule = oper.build_rule(vector)

        antecedent, consequence = oper.get_ant_con(rule, cut)

        support, confidence = oper.calculate_support_confidence(
                antecedent, consequence, transactions)

        self.assertEqual(antecedent, antecedent_a)
        self.assertEqual(consequence, consequence_a)
        self.assertEqual(support_a, support)
        self.assertEqual(confidence_a, confidence)
