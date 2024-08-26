A scalable solution for managing custom fields, enabling corporates to tailor the platform to their unique needs.
This solution:
1. Supports diverse data types: Accommodate text, numbers, dates, dropdowns, and other data formats to capture various information points.
2. CRUD operations: Support Create, Read, Update, and Delete actions on custom field data, ensuring data integrity and user control.
3. Robustness and scalability: handles diverse volumes and types of custom fields efficiently, maintaining performance and stability.

Low level design of customer fields against the scalability - 10k custom fields and entering 1M entries for each.


Approach 1
| Custom Fields |                     |        |                   |         |            |            |
| ------------- | ------------------- | ------ | ----------------- | ------- | ---------- | ---------- |
| id            | name                | type   | validation_rules  | options | created_at | updated_at |
| 1             | Product description | text   | {max_length = 50} | null    | 24/08/2024 | null       |
| 2             | Phone number        | number | {max_length = 10} | null    | 24/08/2024 | null       |

| CustomFieldsValue |           |                 |                       |              |              |            |            |            |            |
| ----------------- | --------- | --------------- | --------------------- | ------------ | ------------ | ---------- | ---------- | ---------- | ---------- |
| id                | entity_id | custom_field_id | value_text            | value_number | valu_boolean | value_date | value_json | created_at | updated_at |
| 1                 | 1         | 1               | Samsung 301 L, 2 Star | null         | null         | null       | null       | 24/08/2024 |            |
| 2                 | 2         | 2               |                       | 99988776655  | null         | null       | null       | 24/08/2024 |            |

Approach 2

 Custom Field |                     |        |         |               |            |            |            |
| ------------ | ------------------- | ------ | ------- | ------------- | ---------- | ---------- | ---------- |
| id           | name                | type   | options | created_by    | created_at | udpated_at | updated_by |
| 1            | Product description | text   | null    | abc@gmail.com | 24/08/2024 | null       | null       |
| 2            | Stock Quantity      | number | null    | abc@gmail.com | 24/08/2024 | null       | null       |
| 3            | Order Date          | date   | null    | abc@gmail.com | 24/08/2024 | null       | null       |

| Custom Field Value |                     |                      |           |                   |            |            |            |
| ------------------ | ------------------- | -------------------- | --------- | ----------------- | ---------- | ---------- | ---------- |
| id                 | custom_field_id(FK) | value                | entity_id | created_by        | created_at | udpated_at | updated_by |
| 1                  | 1                   | Samsung Refrigerator | Samsung   | samsung@gmail.com | 24/08/2024 | null       | null       |
| 2                  | 2                   | 10                   | Samsung   | samsung@gmail.com | 24/08/2024 | null       | null       |
| 3                  | 3                   | 21/08/2024           | Samsung   | samsung@gmail.com | 24/08/2024 | null       | null       |


Analysis and trade offs between approach 1 and 2:
1. Simplicity vs. Data Integrity
Pros:
Simplified Schema: Reduced number of columns in the CustomFieldValue table. Simpler schema and codebase easier to maintain.
Uniform Querying: All custom field values can be queried uniformly without worrying about different data types or handling different columns for different types.
Cons:
Data Integrity: Storing everything as text sacrifices data integrity. For instance, numeric fields won't have the protection of the database ensuring they are actually numeric, and dates might be stored in an incorrect format without validation.
Increased Risk of Invalid Data: Since there is no strict enforcement at the database level, it’s possible to store invalid data (e.g., storing "abc" in a field that is supposed to be numeric).
2. Performance
Pros:
Simple Queries: You can have simpler SQL queries since all values are stored in one column and can be queried using a single column (value).
Cons:
Performance Overhead: Storing everything as text means that for numeric operations (e.g., sorting or filtering by a number range), the database has to cast text to the appropriate type, which adds overhead.
Increased Storage: Storing large amounts of data as text can increase storage requirements.
Indexing Challenges: Indexes on text columns are generally less efficient for numeric or date operations. Especially, If you need to sort, filter, or aggregate based on these fields.
3. Scalability
Pros:
Scalable in Terms of Schema Changes: Adding new types of fields doesn't require changing the database schema, which can be beneficial in a highly dynamic environment where fields are frequently added or changed.
Cons:
Query Complexity and Performance Degradation: As the number of custom fields and entries grows, the system might experience performance bottlenecks due to the need to cast text fields to appropriate types on the fly, especially in a scenario with millions of entries and frequent queries.
Conclusion
Using text to store all custom field values in the CustomFieldValue table simplifies the database schema but comes at the cost of data integrity, performance, and query complexity. This approach is flexible and scalable from a schema management perspective but places a heavier burden on the application layer to enforce data types, validate inputs, and handle conversions. It's generally more suitable for scenarios where flexibility and schema evolution are prioritised over strict data integrity and performance.
For large-scale systems with strict requirements on data integrity, performance, and efficient querying, a more normalised approach with type-specific columns might be better despite the added complexity in schema design.
