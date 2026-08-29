# docker build -f services/core/Dockerfile -t core .
# docker run --rm core sh -c "ls -la /srv; find / -name '.env*' 2>/dev/null"

# gcloud auth application-default login
# gcloud auth application-default set-quota-project app-dev-504613