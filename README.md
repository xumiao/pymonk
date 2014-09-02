**MONK** - social network for A.I.
======

MONK is a distributed interactive machine learning framework for both **users** and **scientists** with a focus on the agility of building and sharing the models. **pymonk** is a version implemented in python.

Big Learning
--------
Big Analytics concerns about the scalability of discovering insights, but Big Learning concerns more about the scalability of discovering **actionable** insights. Purchasing a pregnancy-tester might imply a diaper demand for one woman, but this might fail on many others. At the end of the day, what people really need is the knowledge that can be executed to gain, and the only way to get that knowledge is tying the inputs and the outputs together to maximize the gains. *Apache MLlib*, *Oryx*, *H2O*, *Graph-Lab*, and *Vowpal-wabbit* are the major distributed machine learning projects specialized in different aspects, so what differences MONK brings?

A Monk can be imagined as your intelligent delegate that automates the work for you. How the users interact with Monks and how Monks interact with each other makes it a unique framework with emphasis on efficiently and effectively transfering human intelligence to machines. Somehow, the system is more or less like a social network for the intelligent agents.

**Targeting Scenarios**

1. Device automation through cloud community that tackles the data sparsity and the data privacy problems simultaneously
2. Social recommendation system that recommends items by following your trusted taste or creating your own taste
3. Collaborative research that enables a community to conquer one problem at a time, e.g., gardening ontology building from literatures

By the Users and For the Users
-----

* MONK accepts end users' actions and contexts directly, and learns in near-real-time to keep the "intelligence" up-to-date. 

```python
import monk.core.api as monkapi
monkapi.add_data(john_spam_filter, john, email)
```

* MONK allows a user follow other user's models. The data from all users will contribute to the same model without exposing to each other.

```python
import monk.core.api as monkapi
adam_recipe_recommendation = monkapi.follow(john_recipe_recommendation, 'adam')
```

* MONK allows users' models to be different from each other. Personalization can reduce the model size, improve both the speed and the accuracy. However, too much personalization can hurt because it means "stubbon" and a "lone wolf". A value somewhere between 0 and infinity will get the best value out of both **community knowledge** and **personal experience**.

```python
john_home_temperature_controller.lambda = 1
```

Assisting Scientists
----

* MONK integrates a tagging process, which employs *active learning* algorithms to reduce the tagging efforts to the minimum.

```python
import monk.core.api as monkapi
monkapi.active_train(junk_post_recognizer, issac)
```

* MONK encourages model sharing to speed up *research* work. If adam has built *affective word tagger*, john can build a sentiment model for his project.

```python
sentiment_predication_by_john.requires(affective_prediction_by_adam)
```

* MONK allows easily controlled experimentation for feature engineering. After cloning new models, scientists either re-train on existing data, or evaluates on the forth-coming data to compare the models.

```python
import monk.core.api as monkapi
group1, group2 = monkapi.split_data(some_project, [0.5,0.5])
some_project_dev = monkapi.clone(some_project, group1)
some_project_dev.requires(affective_prediction_by_jefferson)
```

* MONK targets to support advanced supervisions including **self-training**, **co-training** and **weak-supervision**. It has been a perfect example of **transfer learning**.

* MONK targets to support advanced statistical programming, e.g., **BLOG**, **Markov Logic Networks**, and even deep models like **Sum-Product-Networks**.

Architecture
=======

The major architecture issue is how to distribute computations. Unlike map-reduce (spark), all-reduce (vowpal-wabbit), and message-passing (GraphLab), MONK follows **Alternating Direction Method of Multipliers (ADMM)** framework to distribute jobs and adopts an event-driven asynchronous approach to respond users' requests. 

MONK follows the user-locality assumption to divide the batch job with respect to end users, and updating models on users' commands. The leaders will merge the followers' models from time to time, and distribute back to the followers to allow community knowledge spread. It has been proved that the number of iterations between leaders and followers that is required to converge for ADMM is significantly smaller than most of other distributed alogrithms, e.g., parallel SGDs or *shotgun* style updating rules. Therefore, much less stress is put on the network infrastructure. 

In addition, updating models for each user is a real-time task, while merging models from followers is not that time-critical, so we put it in a near-real-time layer. MONK also supports a full batch-mode feature extractions layer that only executes once a while. These three-layer achitecture provides MONK *speeds* and *volumes*.

MONK adopts `Apache Kafka` as the high throughput bus to connect the layers and between layers and roles (users, scientists and admins). Kafka ensures the fault-tolerance and communication consistency for MONK. 


MONK builds on top of the `MongoDB` because of its scalability, full-text indexing, Geo-indexing, and full featured SQL-like language. Its own map-reduce implementation can perform light-weighted batch jobs easily.

Data Structures and Algorithms
======

MONK features a FlexibleVector data structure that extends from SkipList based sparse vector representation to allow smooth transition between dense vector and sparse vector. It allows `O(log(n))` amortized time to perform all operations at any time. It takes advantages of both CPU pre-fetching for dense vector, and linked list for sparse vector. So, the users don't have to pay attention to when to switch from each other, and allow the data and the models to modified at any moments.

Inspired by vowpal wabbit, MONK adopts the **learning reduction** techniques to break any problem down into basic problems, e.g., binary classifications. It abstracts away the learning algorithms from the statistical programming, and allows scientists to do their best inventing better models without worrying about the optimality of the learning algorithms.


Status
=======

**MONK** is under development. If anyone is interested in joining us, please let me know <pacificxumiao@gmail.com>. I am more than happy to share what I know and what I envision.

Features will be supported
=======

1. Featurization
- Distributed feature extraction
- NLP pipeline with NLTK (optional)
- OpenCV pipeline with pycv (optional)
2. Classification and regression
- L2 and L1 regularization
- Continuous ADMM for distributed continuous optimization
- Active learning
- Personalization
3. Recommendation with exploration
- Contextual-based recommendation
- Bandit for exploration
- Different cost function
4. Structured prediction
- Automatic or manual structure learning to improve indexing for faster inference
- Learning reduction to improve the accuracy 
