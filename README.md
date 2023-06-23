
# Inventory Checker

Just a little project that helps me to check inventory for my products in a certain supermarket's web store, and then notifies me if there's any inventory through a Discord channel.

It also allows me to try some technologies such as AWS Lambda and Terraform to automate the deployment of the function.

## Roadmap

- Use a S3 bucket for the origin file (DONE)

- Use a layer to reduce the file uploading time

- Implement a frontend to add items?

- Use a remote backend for Terraform (DONE)


## Usage/Examples
Just create a .tfvars with the following variables:

- market_webhook_url: The URL for the discord channel webhook for the market items

- club_webhook_url: The URL for the discord channel webhook for the club items

- s3_bucket_name: the S3 bucket name in which the json file with the items to check will be and to name it items.json. Here's an example for the contents of the file:



```json
{
    [
        {
            "type": "club",
            "item": "Cat toy",
            "url": "https://www.cluburl.com/product/408888",
            "enabled": false
        },
        {
            "type": "market",
            "item": "Item1",
            "url": "https://www.marketurl.com/product/76519",
            "sucursal": 999,
            "price": 89.00,
            "enabled": true
        }
    ]
}
```

