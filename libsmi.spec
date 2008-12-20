# mib repository
%define mibsdir		%{_datadir}/%{name}/mibs
# pib repository
%define	pibsdir		%{_datadir}/%{name}/pibs

%define	major 2
%define libname %mklibname smi %{major}
%define develname %mklibname smi -d

Summary:	LibSMI deals with SNMP MIBS definitions
Name:		libsmi
Version:	0.4.8
Release:	%mkrel 3
License:	BSD-like
Group:		System/Libraries
URL:		http://www.ibr.cs.tu-bs.de/projects/libsmi/
Source0:	ftp://ftp.ibr.cs.tu-bs.de/pub/local/libsmi/%{name}-%{version}.tar.gz
Patch0:		libsmi-0.4.8-format_not_a_string_literal_and_no_format_arguments.diff
Requires:	coreutils
BuildRequires:	bison
BuildRequires:	flex
BuildRequires:  libtool
BuildRequires:	wget
Buildroot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

%description
This package contains the SMI library and standard IETF and IANA Mibs. This
library provides a programmer-friendly interface to access MIB module
information.

System config file: %{_sysconfdir}/smi.conf
User config file:   .smirc

%package -n	%{libname}
Summary:	LibSMI deals with SNMP MIBS definitions
Group:          System/Libraries
Provides:	libsmi = %{version}-%{release}
Requires:	%{name}-mibs-std
Conflicts:	smi-tools < 0.4.5-1

%description -n	%{libname}
This package contains the shared SMI libraries and standard IETF and IANA Mibs.
This library provides a programmer-friendly interface to access MIB module
information.

System config file: %{_sysconfdir}/smi.conf
User config file:   .smirc

%package -n	%{develname}
Summary:	Development tools for LibSMI
Group:		Development/Other
Requires:	%{libname} = %{version}
Provides:	smi-devel = %{version}-%{release}
Provides:	libsmi-devel = %{version}-%{release}
Obsoletes:	%{mklibname smi 2 -d}

%description -n	%{develname}
This package contails the include files and static library needed to develop
applications based on the SMI Library

%package	mibs-std
Summary:	Standard MIB files for LibSMI
Group:		System/Libraries
Requires:	smi-tools = %{version}

%description	mibs-std
This package contains standard MIB files for use with the SMI Library:

 o IETF - standard MIBS for SNMP, SNMPv2, interfaces, IP, 
 o IANA - standard identifiers for protocols, ifType, etc.

%package	mibs-ext
Summary:	Extended MIB files for LibSMI
Group:		System/Libraries
Requires:	smi-tools = %{version}

%description	mibs-ext
This package contains Extended MIB files for use with the SMI Library:

 o IRTF - SMIng oids, extensions, types 
 o TUBS - MIBS for the Technical University of Braunschweig

%package -n	smi-tools
Summary:	LibSMI tools
Group:          Networking/Other
Requires:	%{libname} = %{version}
Requires:	wget

%description -n	smi-tools
This package contains the LibSMI tools.

%prep

%setup -q -n %{name}-%{version}
%patch0 -p0 -b .format_not_a_string_literal_and_no_format_arguments

%build

%configure2_5x \
    --with-mibdir=%{mibsdir} \
    --with-pibdir=%{pibsdir} \
    --with-smipath=%{mibsdir}/site:%{mibsdir}/ietf:%{mibsdir}/iana \
    --enable-smi \
    --enable-sming

%make

%check
# fails a couple of tests (2 in {0.4.4, 0.4.5})
make check ||:

%install
rm -rf %{buildroot}

%makeinstall_std

# something broke here...
rm -f %{buildroot}%{pibsdir}/*PIB*
rm -f %{buildroot}%{pibsdir}/*SPPI*
install -m0644 pibs/ietf/* %{buildroot}%{pibsdir}/ietf/
install -m0644 pibs/site/* %{buildroot}%{pibsdir}/site/
install -m0644 pibs/tubs/* %{buildroot}%{pibsdir}/tubs/
find %{buildroot}%{pibsdir}/ -name "Makefile*" | xargs rm -f

install -d %{buildroot}%{_sysconfdir}

cat > smi.conf << EOF
#
# smi.conf - Global/User SMI configuration file.
#
# See smi_config(3) for detailed information on configuration files.
#

# Extend (note the semicolon) the libsmi default module search path.
#path :%{mibsdir}/site
#path :%{mibsdir}/iana
#path :%{mibsdir}/ietf

# Add a private directory.
#path :/home/strauss/lib/mibs

# EXPERIMENTAL: Add a caching method (works only on UNIX systems). 
# NOTE: the cache directory must exist and permissions must be
# handled appropriately. A simple but insecure way is to apply
# a tmp flag to the directory (chmod 1777 /usr/local/share/mibs/cache).
#cache /usr/local/share/mibs/cache /usr/local/bin/smicache -d /usr/local/share/mibs/cache -p http://www.ibr.cs.tu-bs.de/projects/libsmi/smicache/

# Don't show any errors by default.
level 0

# Preload some basic SMIv2 modules.
load SNMPv2-SMI
load SNMPv2-TC
load SNMPv2-CONF

# Make smilint shout loud to report all errors and warnings.
smilint: level 9

# But please don't claim about any names longer than 32 chars.
# (note: this is the prefix of errors namelength-32-module,
#  -type, -object, -enumeration, and -bit)
smilint: hide namelength-32

# Preloading some more modules for special applications.
tcpdump: load DISMAN-SCRIPT-MIB
tcpdump: load IF-MIB
smiquery: load IF-MIB
EOF

install -m0644 smi.conf %{buildroot}%{_sysconfdir}/smi.conf

install -d %{buildroot}%{mibsdir}/site
install -d %{buildroot}%{pibsdir}/site

%if %mdkversion < 200900
%post -n %{libname} -p /sbin/ldconfig
%endif

%if %mdkversion < 200900
%postun -n %{libname} -p /sbin/ldconfig
%endif

%post mibs-ext
## Append to config file: path for irtf and tubs
if test ! -f %{_sysconfdir}/smi.conf; then echo "# Generated by %{name}" > %{_sysconfdir}/smi.conf ; fi
for DIR in irtf tubs ; do
  if %__grep -q -e "^path.*%{mibsdir}/${DIR}" %{_sysconfdir}/smi.conf ; then continue; fi
  echo "path :%{mibsdir}/${DIR}" >> %{_sysconfdir}/smi.conf
done

%clean
rm -rf %{buildroot}

%files -n %{libname}
%defattr(-,root,root,0755)
%doc ANNOUNCE COPYING README THANKS smi.conf-example
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/smi.conf
%attr(0755,root,root) %{_libdir}/lib*.so.*

%files -n %{develname}
%defattr(-,root,root,0755)
%doc TODO doc/draft-irtf-nmrg-sming-02.txt
%attr(0644,root,root) %{_includedir}/*.h
%attr(0755,root,root) %{_libdir}/lib*.so
%attr(0644,root,root) %{_libdir}/lib*.a
%attr(0755,root,root) %{_libdir}/lib*.la
%attr(0644,root,root) %{_datadir}/aclocal/*.m4
%attr(0644,root,root) %{_libdir}/pkgconfig/libsmi.pc
%attr(0644,root,root) %{_mandir}/man3/libsmi.3*
%attr(0644,root,root) %{_mandir}/man3/smi_*.3*

%files mibs-std
%defattr(-,root,root,0755)
%dir %{mibsdir}
%dir %{mibsdir}/iana
%dir %{mibsdir}/ietf
%dir %{mibsdir}/site
%{mibsdir}/iana/*
%{mibsdir}/ietf/*

%files mibs-ext
%defattr(-,root,root,0755)
%dir %{mibsdir}/irtf
%dir %{mibsdir}/tubs
%{mibsdir}/irtf/*
%{mibsdir}/tubs/*
%dir %{pibsdir}
%dir %{pibsdir}/ietf
%dir %{pibsdir}/site
%dir %{pibsdir}/tubs
%{pibsdir}/ietf/*
%{pibsdir}/tubs/*

%files -n smi-tools
%defattr(-,root,root,0755)
%attr(0755,root,root) %{_bindir}/smi*
%attr(0644,root,root) %{_mandir}/man1/smi*.1*
