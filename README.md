**MONK** 
======

MONK is a distributed interactive machine learning framework for both **users** and **scientists** with a focus on the agility and the sharing of the models. **pymonk** is a python implementation version.

Big Learning
--------
Big Analytics concerns about the scalability of discovering insights, but Big Learning concerns more about the scalability of discovering **actionable** insights. Purchasing a pregnancy-tester might imply a diaper demand for one woman, but this might fail on many others. At the end of the day, what people really need is the knowledge that can be executed to gain, and the only way to get it is to tie the inputs and the outputs together. *Apache MLlib*, *Oryx*, *H2O*, *Graph-Lab*, and *Vowpal-wabbit* are the major distributed machine learning projects specialized in different aspects, so what differences **MONK** makes?

By the Users and For the Users
-----
The end user is always the primary factor in **MONK**. MONK can be imagined as your intelligent delegate that automates the work for you. How the users interact with **MONK** and how **MONKs** interact with each other makes it a unique framework.

* MONK accepts end users' actions and contexts directly, and learns in near-real-time to keep the "intelligence" up-to-date. 

```python
import monk.core.api as monkapi
monkapi.add_data(john_spam_filter, john, email)
```

* MONK allows a user follow other user's models. The data from all users will contribute to the same model without exposing to each other.

```python
import monk.core.api as monkapi
adam_book_recommendation = monkapi.follow(john_book_recommendation, 'adam')
```

* MONK allows users' models to be different from each other. Personalization can reduce the model size, improve both the speed and the accuracy. However, too much personalization can hurt because it means "stubbon" and a "lone wolf". A value somewhere between 0 and infinity will get the best value out of both **community knowledge** and **personal experience**.

```python
home_temperature_controller.lambda = 1
```

Assist Scientists
----

* MONK integrates a tagging process, which employs *active learning* algorithms to reduce the tagging efforts to the minimum.

```python
import monk.core.api as monkapi
monkapi.active_train(turtle, user)
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

The major architecture issue is how to distribute computations, and MONK follows **Alternating Direction Method of Multipliers (ADMM)** framework. It has been proved that the convergence rate of ADMM is superior than most of other alogrithms, e.g., parallel SGDs or *shotgun* style updating rules. In addition, we divide the learning batch with respect to different users, updating models for each user is a real-time task, while merging models from all users is relatively slow-paced. MONK also supports a full batch-mode feature extractions layer which can be considered to be done once a while. Therefore, these three-layer achitecture provides MONK **speeds** and **volumes**.

**MONK** adopts `Apache Kafka` as the bus to connect the layers with roles (users, scientists and admins). Any **MONK** node fails, the restarter picks up from where it left, and due to the partition setting, the messages will be guaranteed to be delivered to the same **MONK** node for the same user.


**MONK** builds on top of the **MongoDB** because of its scalability, full-text indexing, Geo-indexing, and full featured SQL-like language. Its own **MapReduce** implementation can perform light-weighted batch jobs like feature extractions.


Targeting Scenarios
=======

* Device automation through community that can relieve the data sparsity and the data privacy problems
* Social recommendation system that recommends items by following your trusted taste or creating your own taste
* Collaborative researching that enables a community to conquer one problem at a time, e.g., ontology building from literatures


Status and Roadmaps
=======

**MONK** is under development. If anyone is interested in joining us, please let me know <pacificxumiao@gmail.com>. I am more than happy to share what I know and what I envisioned.

















