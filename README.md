[![Build Status](http://jenkins.projectmeniscus.org/job/Meniscus/badge/icon)](http://jenkins.projectmeniscus.org/job/Meniscus/)

# Meniscus

Meniscus is a Python based system for event collection, transit and processing in the large. It's primary use case is for large-scale Cloud logging, but can be used in many other scenarios including usage reporting and API tracing.

There is lots of documentation in the [Github Wiki](https://github.com/ProjectMeniscus/meniscus/wiki). For additional help or questions, jump on the [mailing list](https://groups.google.com/forum/#!forum/meniscus) or ask on StackOverflow with the [#meniscus](http://stackoverflow.com/questions/tagged/meniscus) tag. 

## The Problem

Software systems produce events but often do so in non-uniform ways. A system may log information to a file in a grammar that requires comprehension to extract meaning from the output. A system may also send events to other systems in a structured manner such as REST. Other systems may event output events directly into a database for storage or pass them to a queue for distribution to interested consumers.

In highly diverse, clustered environments like those seen in many OpenStack deployments, the system event landscape can become complex, difficult to manage and over time become opaque to the point where events generated no longer provide value. The information in many of these events have definite business value, whether it be to meter a tenant or to communicate that a portion of the cluster has been damaged or degraded. Therefore, it’s imperative, despite the complexity of the event ecosystem, to capture this information in a standardized and scalable manner.

## Getting Started

* Installation
* [Development Environment Set Up](https://github.com/ProjectMeniscus/meniscus/wiki/Creating-a-development-environment-to-work-with-Meniscus)
* [API Documentation](https://github.com/ProjectMeniscus/meniscus/wiki#api-documentation)
* [Technology & standards](https://github.com/ProjectMeniscus/meniscus/wiki/Technology-and-Standards)
* FAQ

## Current Plans

The entirely of Meniscus can be broken down into six distinct operational functions. 

1. Collection
2. Transport
3. Storage
4. Event Processing & Enhancement
5. Complex Event Processing
6. Analytics

Depending on how these are combined, the offering can be used for application logging, usage calculation, performance monitoring or any other event management operation. More information on these areas can be found [on the wiki](https://github.com/ProjectMeniscus/meniscus/wiki/Operational-Functions).

## Design Goals

* Stress the utilization of standards, of which there are many for this problem domain.
* Adhere to compliance rules related to system and application event logging.
* Support multiple tenants in secure isolation.
* Impact target installations as little as possible.
* Allow for direct application integration via a structured publication endpoint.
* Design for platform efficiency, durability and scalability.
* Provide administrators with text search capability of all events processed and stored for a given tenant.
* Provide well formed a set of API specifications for configuration and administration.
* Provide common sinks for already existing systems such as [Ceilometer](https://wiki.openstack.org/wiki/Ceilometer).
* The architecture must be resilient to multiple failures.
* Must support end-to-end run-time mutability.
