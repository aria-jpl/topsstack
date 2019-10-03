FROM hysds/pge-base:latest

# Set to root user
USER root

# Install ISCE2
RUN source /opt/conda/bin/activate root \
 && conda install -c conda-forge isce2

# Install directory
ENV ISCE_HOME /opt/conda/lib/python3.7/site-packages/isce
ARG ISCE_APPS_DIR=${ISCE_HOME}/applications
ARG STACK_INSTALL_DIR=${ISCE_HOME}/components/contrib/stack
ARG TOPSSTACK_INSTALL_DIR=${STACK_INSTALL_DIR}/topsStack
ARG TOPSSTACK_COPY_DIR=/root/topsStack
ENV PATH ${PATH}:${ISCE_APPS_DIR}:${TOPSSTACK_INSTALL_DIR}

# Copy stack processor code into docker image
COPY topsStack $TOPSSTACK_COPY_DIR

# Copy stack processor code into install directory; Adjust group permissions
# so stack processor and associated logs can be written.
RUN mkdir -p $STACK_INSTALL_DIR \
 && cp -r $TOPSSTACK_COPY_DIR $STACK_INSTALL_DIR \
 && rm -rf $TOPSSTACK_COPY_DIR

RUN cd /etc/yum.repos.d/ && \
    wget http://download.opensuse.org/repositories/home:/tange/CentOS_CentOS-6/home:tange.repo && \
    yum install parallel && \
    yum clean all

# Set to ops user
USER ops

# Copy topsStack PGE into docker image
COPY . /home/ops/verdi/ops/topsstack

# Change to work directory
WORKDIR /home/ops

# Run shell
CMD ["/bin/bash", "--login"]
