# SOFTWARE REQUIREMENTS SPECIFICATION

## Prepared by

Mykyta Kyt Alex Zhytnyk

1. Introduction

  1. Purpose
  2. References

2. Overall Description

  1. Product perspective
  2. Product features
  3. Operating environment
  4. Design and implementation constraints

3. System features

  1. Description and priority

4. External interface requirements

  1. User Interfaces
  2. Hardware Interfaces

5. Non functional requirements

  1. Software quality attributes
  2. Security requirements

## 1\. Introduction

### 1.1 Purpose

The purpose of this document is to describe the equipment and employee's accounting system in the company. Of itself, it will represent a database to which you can connect through the web client. The database will have a lot of features such as auto back-up, export to .csv or .xls files, create reports, create new fields, delete and update them. It will be possible to generate inventory labels, which means qr codes. The database will contain all the information about employees and equipment. This product will be able to organize everything and make life easier.

### 1.2 References

1. <https://www.wikiwand.com/en/Flask_(web_framework>) : Flask is a python based lightweight web application framework.
2. <https://www.postgresql.org/> : PostgreSQL is a powerful, open source object-relational database system.
3. <https://pypi.org/project/qrcode/>: Python's library for generating unique qr code for each device.
4. <https://cutt.ly/zf7MkUX> : This article is an explanation of how to connect PostgreSQL with Flask.
5. <https://hydra.cc/docs/intro/> : Hydra is an open-source Python framework that simplifies the development of research and other complex applications.

## 2\. Overall Description

### 2.1 Product perspective
