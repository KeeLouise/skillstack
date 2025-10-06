				
## Github URL:
   
    Github repository: https://github.com/KeeLouise/skillstack

## Render URL:

    Render URL: https://skillstack-1bx8.onrender.com

## Django Admin Login:

    Username: admin
    Password: Super2025***

## Project Goals  

SkillStack is a simple yet sleek project management web app built with Django. The main goal of my project is to help developers create projects, invite collaborators to work with them, share files, and keep everything in one place. Each user gets a dashboard to quickly see their own projects as well as projects they’ve been invited to. It also includes a built-in messaging system, so conversations stay connected to the projects.  

The idea is to make collaboration easier for small teams or individuals without needing to use multiple different tools.  

## Challenges Faced  

While building SkillStack, there were a few challenges:  

- **User accounts and permissions**: It was important to make sure project owners and collaborators only have the right level of access (for example, only owners can delete a project).  
- **Error handling**: Setting up clear custom error pages (like 404 and 500) so users don’t see confusing error messages.  
- **Emails**: Sending invitations to people who don’t yet have an account, while notifying existing users, required careful setup.
- **Database migrations**: At times migrations did not sync properly, which caused errors when deploying. This meant manually checking and resetting migrations until the database matched the models.   
- **Deployment issues**: Running the app on Render with `DEBUG=False` caused some problems with static files and signals, which took some troubleshooting to fix.  

These challenges were a good learning experience and helped strengthen the project.  

## Room for REST API Expansion  

Right now, SkillStack uses server-side pages, but there’s room to grow by adding a REST API. This would make it easier to connect with mobile apps, front-end frameworks or even third-party services. Possible API features include:  

- **Project endpoints**: Create, update, and view projects through an API.  
- **Messaging API**: Send and receive messages between users.  
- **Collaborator management**: Invite, accept, or remove collaborators without needing the web interface.  
- **File management**: Upload and download files via an API to connect with cloud storage or other tools.  

Adding an API would make the platform more flexible and useful for future development.  

## List of sources

   desktop-logo.webp - Kiera Reidy (2025) "Skillstack" [image]. Available at: https://github.com/KeeLouise/skillstack (Accessed: 3rd July 2025)
