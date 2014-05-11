**MONK** 
======

MONK is a distributed interactive machine learning framework for both **users** and **scientists** with a focus on the agility and the sharing of the models. **pymonk** is a python implementation version.

Big Learning
--------
Big Analytics concerns about the scalability of discovering insights, but Big Learning concerns more about the scalability of discovering **actionable** insights. Purchasing a pregnancy-tester might imply a diaper demand for one woman, but this might fail on many others. At the end of the day, what people really want is the knowledge that can be executed to gain, and the only way to find is to tie the inputs and the outputs together. *Apache MLlib*, *Oryx*, *H2O*, *Graph-Lab*, and *Vowpal-wabbit* are some major projects in this area specialized in different aspects, so what is different for **MONK**?

By the Users and For the Users
-----

* MONK accepts end users' actions and contexts directly, and learns in near-real-time to keep the "intelligence" up-to-date. 

```python
import monk.core.api as monkapi
monkapi.add_data(turtle, user, entity)
```

* MONK allows a user follow other user's models. The data from all users will contribute to the same model without exposing to each other.

```python
import monk.core.api as monkapi
monkapi.follow(turtle, user)
```

* MONK allows users' models to be different from each other. Personalization reduces the model size, improves both the speed and the accuracy. 

```python
turtle.lambda = 1
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
sentiment_turtle_by_john.requires(affective_turtle_by_adam)
```

* MONK allows easily controlled experimentation for feature engineering. After cloning new turtles, scientists either re-train on existing data, or evaluates on the forth-coming data to compare the models.

```python
import monk.core.api as monkapi
group1, group2 = monkapi.split_users(turtle)
turtle_dev = monkapi.clone(turtle, group1)
turtle_dev.requires(affective_turtle_by_jefferson)
```

* MONK targets to support advanced supervisions including **self-training**, **co-training** and **weak-supervision**. It has been a perfect example of **transfer learning**.

* MONK targets to support advanced statistical programming, e.g., **Bayesian Networks**, **Markov Logic Networks**, and even deep models like **Sum-Product-Networks**.

Architecture
-----

The major architecture issue is how to distribute computations, and MONK follows **Alternating Direction Method of Multipliers (ADMM)** framework. It has been proved that the convergence rate of ADMM is superior than most of other alogrithms, e.g., parallel SGDs or *shotgun* style updating rules. In addition, we divide the learning batch with respect to different users, updating models for each user is a real-time task, while merging models from all users is relatively slow-paced. MONK also supports a full batch-mode feature extractions layer which can be considered to be done once a while. Therefore, these three-layer achitecture provides MONK **speeds** and **volumes**.

To connect layers together with roles (users and scientists), MONK depends on `Apache Kafka`.


















