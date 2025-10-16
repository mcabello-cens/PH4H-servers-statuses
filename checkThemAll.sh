echo "Checking servers... it takes a while"

bash checkServer.sh http://conn23.msal.gov.ar:8180/fhir http://node-ARG.org/terminolgy 546301000221104 ARGENTINA & \
bash checkServer.sh http://157.245.123.204:8180/fhir http://node-BS.org/terminology 1003755004 BAHAMAS-ALLEN & \
bash checkServer.sh http://tst.regunit.health.gov.bb/term/fhir http://node-acme.org/terminology 0 BARBADOS-SHELDON & \
bash checkServer.sh http://190.93.82.203:8180/fhir http://node-acme.org/terminology 0 BELIZE & \
bash checkServer.sh https://snowstorm.ips.hsl.org.br http://node-acme.org/terminology 0 BRAZIL & \
bash checkServer.sh https://hcsba-api.hcsba.cl/terminologico/1/fhir http://node-acme.org/terminology 0 CHILE & \
bash checkServer.sh http://201.191.3.209:8180/fhir http://node-acme.org/terminology 1 COSTARICA & \
bash checkServer.sh https://test-ips-snowstorm.msp.gob.ec/fhir http://node-acme.org/terminology 6 ECUADOR & \
bash checkServer.sh http://lacpass-dev.salud.gob.sv:8080/snowstorm/fhir http://node-acme.org/terminology 1 SALVADOR & \
bash checkServer.sh http://fhir.mspas.gob.gt:8180 http://fhir.mspas.org/terminology A-11 GUATEMALA & \
bash checkServer.sh http://181.210.30.59:8180/fhir http://node-acme.org/terminology A02BC0100 HONDURAS & \
bash checkServer.sh http://190.34.154.93:8180/fhir http://racsel.org/antecedentes E03.9 PANAMA & \
bash checkServer.sh https://snowstorm.mspbs.gov.py/fhir http://node-acme.org/terminology 33 PARAGUAY & \ 
bash checkServer.sh https://dyakuter.minsa.gob.pe/fhir http://node-PE.org/terminology 90633.01 PERU & \
bash checkServer.sh http://154.38.173.158:8180/fhir http://node-x.org/terminology C910 REPDOM & \
bash checkServer.sh http://186.179.201.48:8080/fhir http://node-acme.org/terminology 0 SURINAME & \
bash checkServer.sh http://179.27.170.27:8180/fhir http://node-UY.org/terminology 10 URUGUAY

echo "Finished"
