# Verilator Python Wrapper

An example project that provides a Python wrapper around a Verilatlated module
and builds a complex testbench around it.

## Build and Run

```bash
./example.py
```

The testbench script in combination with the *vpw* package will take the
SystemVerilog RTL files within the 'hdl' directory and creates a pybind11
shared object that is then used by the testbench script to interact with the
module.

## Install

Install the package directly from GitHub using the follower command.

```bash
pip install git+git://github.com/bmartini/vpw-testbench.git
```

Or to upgrade an already installed VPW package.

```bash
pip install --upgrade git+git://github.com/bmartini/vpw-testbench.git
```

## Perquisites

The following packages and programs need to be installed to get VPW working.

### Python packages

Besides the default python install the following packages need to be installed.

```bash
python3 -m pip install typing parsy pybind11
```

### Verilator

Download and install the Verilator simulator.

```bash
sudo apt-get install -y \
    ccache zlib1g autoconf git python3 make g++ ca-certificates \
    flex bison libfl2 libfl-dev zlibc zlib1g-dev libgoogle-perftools-dev numactl

git clone https://github.com/verilator/verilator.git
cd verilator
git checkout stable
autoconf
./configure
make -j `nproc`
sudo make install
cd ..
rm -rf verilator
```

### GTKWave (Optional)

To view the wave forms created by the testbench I recommend GTKWave. The
easiest way to install it is via installing Icarus Verilog (iverilog).

```bash
git clonce git://github.com/steveicarus/iverilog.git
cd iverilog
sh autoconf.sh
./configure
make
sudo make install
```

## Documentation

Explanation of use can be found [here](https://bmartini.github.io/vpw-testbench).
