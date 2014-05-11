**MONK** 
======

MONK is a distributed interactive machine learning framework for both **users** and **scientists** with a focus on the agility of building and sharing the models. **pymonk** is a python implementation version.

Big Learning
--------
Big Analytics concerns about the scalability of discovering insights, but Big Learning concerns more about the scalability of discovering **actionable** insights. Purchasing a pregnancy-tester might imply a diaper demand for one woman, but this might fail on many others. At the end of the day, what people really need is the knowledge that can be executed to gain, and the only way to get that knowledge is tying the inputs and the outputs together to maximize the gains. *Apache MLlib*, *Oryx*, *H2O*, *Graph-Lab*, and *Vowpal-wabbit* are the major distributed machine learning projects specialized in different aspects, so what differences MONK brings?

A Monk can be imagined as your intelligent delegate that automates the work for you. How the users interact with Monks and how Monks interact with each other makes it a unique framework with emphasis on efficiently and effectively transfering human intelligence to machines. Somehow, the system is more or less like a **social network for the intelligent agents**.

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

Assist Scientists
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

The major architecture issue is how to distribute computations, and MONK follows **Alternating Direction Method of Multipliers (ADMM)** framework. It has been proved that the convergence rate of ADMM is superior than most of other alogrithms, e.g., parallel SGDs or *shotgun* style updating rules. In addition, we divide the learning batch with respect to different users, updating models for each user is a real-time task, while merging models from all users is relatively slow-paced. MONK also supports a full batch-mode feature extractions layer which can be considered to be done once a while. Therefore, these three-layer achitecture provides MONK *speeds* and *volumes*.

MONK adopts `Apache Kafka` as the bus to connect the layers with roles (users, scientists and admins). Any Monk fails, the restarter picks up from where it left, and due to the partitioning in Kafka, the messages are guaranteed to be delivered to the same Monk for the same user.


MONK builds on top of the `MongoDB` because of its scalability, full-text indexing, Geo-indexing, and full featured SQL-like language. Its own map-reduce implementation can perform light-weighted batch jobs like feature extractions easily.


Targeting Scenarios
=======

* Device automation through cloud community that tackles the data sparsity and the data privacy problems simultaneously
* Social recommendation system that recommends items by following your trusted taste or creating your own taste
* Collaborative research that enables a community to conquer one problem at a time, e.g., gardening ontology building from literatures


Status
=======

**MONK** is under development. If anyone is interested in joining us, please let me know <pacificxumiao@gmail.com>. I am more than happy to share what I know and what I envisioned.

















