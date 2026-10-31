# Docker: Your Friendly Container Companion

Docker lets you package an application and all its dependencies into a single, lightweight unit called a **container**. Think of it as a portable, self‑contained box that runs the same way on your laptop, a university server, or a cloud instance. This consistency eliminates the classic “it works on my machine” problem and speeds up collaboration among classmates and professors.

A Docker **image** is the read‑only blueprint that describes the software stack—operating system, libraries, runtime, and your code. When you run an image, Docker creates a **container**, a running instance of that blueprint. You can build images with a simple `Dockerfile`, a text file that lists the steps Docker should follow, and then share the image via Docker Hub or a private registry.

In practice, Docker is used for everything from local development to continuous integration pipelines. Students can spin up a database, a web server, and a front‑end app in seconds, all isolated from each other. It also makes it easy to replicate a production environment on a university cluster, ensuring that experiments and projects run consistently across different machines.

> **Tip:** Use `docker-compose.yml` to orchestrate multiple containers (e.g., a web app with a database). It lets you define services, networks, and volumes in one file and start everything with a single `docker compose up` command.