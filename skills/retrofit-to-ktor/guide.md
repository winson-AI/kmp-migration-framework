# Retrofit to Ktor Migration Guide

This guide provides instructions for migrating a Retrofit `ApiService` interface to a Ktor `HttpClient`.

## Key Differences

- **Annotations:** Retrofit uses annotations (`@GET`, `@POST`, `@Path`, etc.) to define API endpoints. Ktor uses a programmatic, builder-style approach.
- **Client Creation:** In Retrofit, you build a `Retrofit` instance and then create an implementation of your interface. In Ktor, you create an `HttpClient` instance and make direct calls with it.
- **Suspend Functions:** Both libraries use `suspend` functions for asynchronous operations, so the core logic remains similar.

## Migration Steps

1.  **Create a Ktor `HttpClient`:** In your KMP shared module, create a single `HttpClient` instance that can be shared across your application.

    ```kotlin
    // commonMain
    import io.ktor.client.*
    import io.ktor.client.engine.cio.*

    val client = HttpClient(CIO)
    ```

2.  **Convert Retrofit interface to a Ktor class:** Create a new class (e.g., `UserKtorService`) that takes the `HttpClient` as a constructor parameter.

3.  **Implement the API calls:** For each method in the Retrofit interface, create a corresponding method in the new Ktor class that makes the API call using the `HttpClient`.

    **Retrofit Example:**
    ```kotlin
    interface ApiService {
        @GET("users/{id}")
        suspend fun getUser(@Path("id") id: String): User
    }
    ```

    **Ktor Example:**
    ```kotlin
    // commonMain
    import io.ktor.client.call.*
    import io.ktor.client.request.*

    class UserKtorService(private val client: HttpClient) {
        suspend fun getUser(id: String): User {
            return client.get("https://api.example.com/users/$id").body()
        }
    }
    ```
4. **Dependency Injection:** Update your dependency injection framework to provide the Ktor service instead of the Retrofit one.
