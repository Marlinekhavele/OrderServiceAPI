# Backend engineering task

### Intro 

At lemon.markets 🍋 we are building the leading European API-first investment platform. We are on a mission to make investing easy, accessible and transparent for everyone.


The challenge is a simplified version of what we are dealing with at lemon.markets.

## Your task

We would like you to develop a simple REST API using Python that allows users to create stock orders so that the following requirements are fulfilled:
1. A valid request to `POST /orders` must result in the order being stored in a database of your choice.
   * These are the expected fields of an order: 

        | Field        | Type    | Description                                                      |
        |--------------|---------|------------------------------------------------------------------|
        | instrument   | string  | ISIN of the stock to be traded (e.g. `DE000A0Q4RZ3`)             |
        | type         | string  | Type of the order, either `market` or `limit`                    |
        | quantity     | integer | Number of stocks to be traded                                    |
        | side         | string  | Either `buy` or `sell`                                           |
        | limit_price  | float   | Limit price for limit orders (only if type is `limit`)           |
   
2. The created order must be placed at the stock exchange.
    * Create a dummy function that mimics the behavior of placing an order at a stock exchange. The function should:
      * Occasionally fail (around 10% of the time) by raising a custom `OrderPlacementError` to simulate unreliable connectivity ;
      * Introduce a short delay (about 0.5 seconds) to represent the cost of a slow external operation ;
      * Pseudo-code:
        ```text
        function place_order(order):
           if random chance (10%):
              raise OrderPlacementError("Failed to place the order at the stock exchange")
    
           wait 0.5 seconds  # simulate expensive operation
        ```
        
3. The endpoint must return a status code of 201 and the created order details, provided that the order has been saved in the database **AND** it is guaranteed that the order **will** be placed on the stock exchange.  
4. In the case of an error in the endpoint, it must return the status code 500 and the body `{"message": "Internal server error while placing the order"}` 
5. The API should be highly scalable and reliable. The reliability of the stock exchange must not impact the reliability of the `POST /orders` endpoint


Additionally, please add some tests and document how you would test the application as a whole and its pieces.
Please provide a Python implementation

Please include a `solution.md` file where you document your decisions, assumptions, and also improvements you would like to incorporate in the future.

We value your time ⏰, so we do not expect you to spend more than 4 hours preparing the solution. 🤗 
Focus on implementing the main task first and afterwards jump on additional improvements as you see fit.

### Tech stack
You are free to use any libraries, frameworks, or technologies you prefer. If you’re interested, here’s a peek at what we usually work with:
* [Python](https://www.python.org/)
* [FastAPI](https://fastapi.tiangolo.com/)
* [Docker & docker-compose](https://www.docker.com/)


### Bonus tasks
* Feel free to add a Dockerfile & compose file to run the application and the database.


###  Everything process related
Please create a fork or clone of this repository, commit all of your work to a new branch, and provide us with a link to the solution via mail 📩, at least 6h before the review meeting.

Feel free to use AI tools (e.g. Copilot, ChatGPT, etc.) as you see fit. We are interested in your approach and decision-making, whether you use AI or not.
