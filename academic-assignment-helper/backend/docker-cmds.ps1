# to get to database of postgress 
#docker exec -it academic_postgres psql -U postgres -d academic_helper 
# to see all databases
# \l
# to connect to a database
# \c academic_helper
# to see all tables
# \dt
# to see the schema of a table
# \d tablename
# to exit psql
# \q

# docker-compose down -v
# docker-compose up --build

# docker fast API cmds
# uvicorn main:app --reload --host


# to use pgadmin in docker follow these steps
# 1. pull the pgadmin image
#    docker pull dpage/pgadmin4
# 2. run the pgadmin container
#    docker run -p 8080:80 `
#      -e "PGADMIN_DEFAULT_EMAIL=afritioalberts1216@gmail.com" `
#      -e "PGADMIN_DEFAULT_PASSWORD=0904161978" `
#      --name pgadmin4 `
#      -d dpage/pgadmin4
# 3. Access pgAdmin in your browser at http://localhost:8080
# 4. Add a new server in pgAdmin using your Postgres container's host, port, username, and password.
# 5. You can now manage your Postgres databases through the pgAdmin web interface.
# to stop and remove the pgadmin container
# docker stop pgadmin4
# docker rm pgadmin4




#n8n-nodes-docx-converter, not to immediately appear after being installed in a Docker environment.
# docker exec -it academic_n8n npm install n8n-nodes-docx-converter
#The correct command to install the package to the n8n nodes directory within the container is generally:
#docker exec -it academic_n8n npm install n8n-nodes-docx-converter --prefix=/home/node/.n8n/nodes


# To back up the PostgreSQL database to a SQL file with a timestamp
#docker exec -t academic_postgres pg_dump -U postgres academic_helper > "academic_assignment_helper_backup_$(Get-Date -Format "yyyy_MM_dd_HH").sql"