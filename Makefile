default:
	echo "resetdb | citus-up | citus-down"

resetdb:
	psql -U rowboat --dbname rowboat --host localhost --port 5444 -f schema/guilds.sql || true
	psql -U rowboat --dbname rowboat --host localhost --port 5444 -f schema/users.sql || true
	psql -U rowboat --dbname rowboat --host localhost --port 5444 -f schema/messages.sql || true

citus-up:
	docker-compose -f etc/citus-docker-compose.yml -p citus up -d

citus-down:
	docker-compose -f etc/citus-docker-compose.yml -p citus down -v
