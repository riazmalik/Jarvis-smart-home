import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import java.io.*;
import java.net.InetSocketAddress;
import java.nio.file.*;

public class Server {

    public static void main(String[] args) throws Exception {

        // Create server on port 8080
        HttpServer server =
                HttpServer.create(
                        new InetSocketAddress(8080),
                        0
                );

        // Website files
        server.createContext("/", Server::handleRequest);

        // Start server
        server.start();

        System.out.println(
            "Website running at: http://localhost:8080"
        );
    }


    // Handle website requests
    public static void handleRequest(
            HttpExchange exchange) throws IOException {

        String path =
                exchange.getRequestURI().getPath();


        // If user opens the main website
        if (path.equals("/")) {

            path = "/index.html";
        }


        // Find requested file
        File file =
                new File(
                    "public" + path
                );


        // File does not exist
        if (!file.exists()) {

            String message =
                    "404 - Page Not Found";

            exchange.sendResponseHeaders(
                    404,
                    message.length()
            );

            OutputStream output =
                    exchange.getResponseBody();

            output.write(
                    message.getBytes()
            );

            output.close();

            return;
        }


        // Read file
        byte[] data =
                Files.readAllBytes(
                        file.toPath()
                );


        // Decide file type
        String type =
                getContentType(file);


        exchange.getResponseHeaders()
                .set(
                    "Content-Type",
                    type
                );


        exchange.sendResponseHeaders(
                200,
                data.length
        );


        OutputStream output =
                exchange.getResponseBody();


        output.write(data);

        output.close();
    }


    // Find the type of file
    public static String getContentType(
            File file) {

        String name =
                file.getName()
                    .toLowerCase();


        if (name.endsWith(".html")) {

            return "text/html";
        }


        if (name.endsWith(".css")) {

            return "text/css";
        }


        if (name.endsWith(".jpg") ||
            name.endsWith(".jpeg")) {

            return "image/jpeg";
        }


        if (name.endsWith(".png")) {

            return "image/png";
        }


        return "text/plain";
    }
}