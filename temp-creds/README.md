• Add IAM Trust Policy for read and list operations
• Update IAM Trust Policy on a given role so that a given user can assume that role temporarily (used jupyterhubProvisioningRole just as proof-of-concept since it has read access)
• Invoke script -- sample output was:

```shell
{
    "AccessKeyId": "ASIA...........",
    "SecretAccessKey": "YgjYVak9Hoq............",
    "SessionToken": "FwoGZXIvYXdzEEEaDFHU6E8/LKXpoElcnC+FJ1chDdhFnTIJz2GQIAdbhO2H3KwXV8DEb4tM307B6U0ysUFUlnkK8Ptxu0HzGwUVgeBZMlXumtRr9Ra8ZozlGycvXPzfP8ASVW7ihI9weig.....................",
    "Expiration": "2024-12-03 16:59:11+00:00"
}
```