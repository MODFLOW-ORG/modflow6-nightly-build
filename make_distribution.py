import sys
import os
import stat
import shutil
import subprocess
import zipfile
import flopy
import pymake
from contextlib import contextmanager


# global variables -- set to most common location relative to this file
DISTRIBUTION_PATH = "./distribution/mf6dev"
MODFLOW6_PATH = "../modflow6"
MODFLOW6_EXAMPLES_PATH = "../modflow6-examples"
FORTRAN_COMPILER = "gfortran"
KEEP = False


@contextmanager
def cwd(path):
    oldpwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(oldpwd)


def paths_for_filename(filename, pth):
    # file occurences of filename in pth and return as list
    # relative to pth
    result = []
    for root, dirs, files in os.walk(pth, topdown=False):
        files = [f for f in files if f == filename]
        for name in files:
            rpath = os.path.relpath(root, start=pth)
            result.append(os.path.join(rpath, name))
    return result


def get_distribution_path(distribution_path=None):
    # set to default if not passed in
    if distribution_path is None:
        distribution_path = DISTRIBUTION_PATH

    # override if -dp argument was set
    for idx, arg in enumerate(sys.argv):
        if arg == "-dp":
            distribution_path = sys.argv[idx + 1]

    # override again if environmental variable set
    env_var = os.environ.get("MODFLOW6_DISTRIBUTION_PATH")
    if env_var is not None:
        distribution_path = env_var

    return distribution_path


def get_modflow6_path(modflow6_path=None):
    # set to default if not passed in
    if modflow6_path is None:
        modflow6_path = MODFLOW6_PATH

    # override if -mf6p argument was set
    for idx, arg in enumerate(sys.argv):
        if arg == "-mf6p":
            modflow6_path = sys.argv[idx + 1]

    # override again if environmental variable set
    env_var = os.environ.get("MODFLOW6_PATH")
    if env_var is not None:
        modflow6_path = env_var

    return modflow6_path


def get_modflow6_examples_path(modflow6_examples_path=None):
    # set to default if not passed in
    if modflow6_examples_path is None:
        modflow6_examples_path = MODFLOW6_EXAMPLES_PATH

    # override if -mf6ep argument was set
    for idx, arg in enumerate(sys.argv):
        if arg == "-mf6ep":
            modflow6_examples_path = sys.argv[idx + 1]

    # override again if environmental variable set
    env_var = os.environ.get("MODFLOW6_EXAMPLES_PATH")
    if env_var is not None:
        modflow6_examples_path = env_var

    return modflow6_examples_path


def get_compiler(fortran_compiler=None):
    set_environmental_var = True

    # set fortran_compiler if -fc argument was set
    for idx, arg in enumerate(sys.argv):
        if arg == "-fc":
            fortran_compiler = sys.argv[idx + 1]
            set_environmental_var = True

    # use environmental variable set if fortran compiler is not set
    if fortran_compiler is None:
        fortran_compiler = os.environ.get("FC")
        if fortran_compiler is not None:
            set_environmental_var = False

    # set to default if not set by command line argument
    # of environmental variables
    if fortran_compiler is None:
        fortran_compiler = FORTRAN_COMPILER

    # set environmental variable
    if set_environmental_var:
        print(f"setting environmental variable FC={fortran_compiler}")
        os.environ["FC"] = fortran_compiler

    return fortran_compiler


def get_keep(keep=None):
    # set to default if not passed in
    if keep is None:
        ckeep = KEEP

    # override if -keep argument was set
    for idx, arg in enumerate(sys.argv):
        if arg in ("-k", "--keep"):
            keep = True

    return keep


def get_platform():
    sys_platform = sys.platform
    platform = "unknown"
    if "linux" in sys_platform:
        platform = "linux"
    elif "darwin" in sys_platform:
        platform = "macos"
    elif "win" in sys_platform:
        platform = "windows"
    return platform


def delete_files(files, pth, allow_failure=False):
    for file in files:
        fpth = os.path.join(pth, file)
        try:
            print("removing...{}".format(file))
            os.remove(fpth)
        except:
            print("could not remove...{}".format(file))
            if not allow_failure:
                return False
    return True


def run_command(
    argv, pth, timeout=None, verbose=True, terminate_on_failure=False
):
    if verbose:
        print(
            "Running system command "
            + f"({' '.join(argv)}) in directory: {pth}"
        )
    with subprocess.Popen(
        argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=pth,
    ) as process:
        try:
            output, unused_err = process.communicate(timeout=timeout)
            buff = output.decode("utf-8")
            ierr = process.returncode
        except subprocess.TimeoutExpired:
            process.kill()
            output, unused_err = process.communicate()
            buff = output.decode("utf-8") + unused_err.decode("utf-8")
            ierr = 100
        except:
            output, unused_err = process.communicate()
            buff = output.decode("utf-8") + unused_err.decode("utf-8")
            ierr = 101
    if terminate_on_failure:
        if ierr != 0:
            if verbose:
                print(f"Failed to execute system command {argv}")
                print(buff)
            raise Exception(
                f"Failed to execute system command {argv}\n"
                + f"return code {ierr}"
            )

    return buff, ierr


def get_is_approved(is_approved):
    for idx, arg in enumerate(sys.argv):
        if arg == "--isApproved":
            is_approved = True
    return is_approved


def set_modflow6_release_info(modflow6_path):
    print(f"Setting the release information for {modflow6_path}")

    isApproved = None
    isApproved = get_is_approved(isApproved)
    version = None
    releaseCandidate = None
    developMode = None

    cmd = ["python", "update_version.py"]
    if isApproved is not None:
        cmd.append("--isApproved")
    if version is not None:
        cmd.append(f"--version {version}")
    if releaseCandidate is not None:
        cmd.append("--releaseCandidate")
    if developMode is not None:
        cmd.append("--developMode")
        cmd.append(developMode)

    pth = os.path.join(modflow6_path, "distribution")
    buff, ierr = run_command(
        cmd,
        pth,
        verbose=True,
        terminate_on_failure=True,
    )

    return


def meson_build_binaries(modflow6_dir, verbose=True):
    # Clean existing builddir
    build_path = os.path.join(modflow6_dir, "builddir")
    print(
        f"cleaning existing meson build directory...'{os.path.abspath(build_path)}'"
    )
    if os.path.isdir(build_path):
        shutil.rmtree(build_path)

    # Create the command list
    abspath_modflow6_dir = os.path.abspath(modflow6_dir)
    cmd_list = [
        "meson",
        "setup",
        "builddir",
        f"--prefix={abspath_modflow6_dir}",
        "--libdir=bin",
    ]

    # use meson to setup the build system
    buff, ierr = run_command(
        cmd_list, modflow6_dir, verbose=True, terminate_on_failure=True
    )

    # run the meson build
    cmd_list = ["meson", "install", "-C", "builddir"]
    buff, ierr = run_command(
        cmd_list, modflow6_dir, verbose=True, terminate_on_failure=True
    )

    return


def initialize_new_distribution(modflow6_path, distribution_path):
    # Create a new folder and set up structure
    print(f"Creating new distribution path: {distribution_path}")
    if os.path.isdir(distribution_path):
        errmsg = (
            "Distribution path cannot already exist. "
            + f"Remove {distribution_path}."
        )
        raise Exception(errmsg)
    else:
        os.makedirs(distribution_path)

    # copy source and sourcebmi to distribution
    print("Copying src and srcbmi...")
    shutil.copytree(
        f"{modflow6_path}/src",
        os.path.join(distribution_path, "src"),
        dirs_exist_ok=True,
    )
    shutil.copytree(
        f"{modflow6_path}/srcbmi",
        os.path.join(distribution_path, "srcbmi"),
        dirs_exist_ok=True,
    )

    # Create subdirectories
    subdirs = [
        "bin",
        "doc",
        "examples",
        # "src",
        # "srcbmi",
        "make",
        "msvs",
        "utils",
    ]

    for sd in subdirs:
        d = os.path.join(distribution_path, sd)
        print(f"Creating directory {d}")
        os.makedirs(d)

    return


def copy_visual_studio_files(modflow6_path, distribution_path):
    # Copy the Visual Studio solution and project files
    flist = [
        os.path.join(modflow6_path, "msvs", "mf6.sln"),
        os.path.join(modflow6_path, "msvs", "mf6.vfproj"),
        os.path.join(modflow6_path, "msvs", "mf6core.vfproj"),
        os.path.join(modflow6_path, "msvs", "mf6bmi.sln"),
        os.path.join(modflow6_path, "msvs", "mf6bmi.vfproj"),
    ]
    print("Copying msvs files")
    for fname in flist:
        destination_path = os.path.join(distribution_path, "msvs")
        print("  {} ===> {}".format(fname, destination_path))
        shutil.copy(fname, destination_path)
    print("\n")
    return


def build_makefile(distribution_path, target="mf6", extrafiles=None):
    print(f"Creating makefile in {distribution_path}")
    makedir = os.path.join(distribution_path, "make")
    with cwd(makedir):
        pymake.main(
            os.path.join("..", "src"),
            target,
            "gfortran",
            "gcc",
            makeclean=True,
            dryrun=True,
            include_subdirs=True,
            makefile=True,
            extrafiles=extrafiles,
        )
        assert os.path.isfile("makefile"), f"Makefile not found in {makedir}"
        assert os.path.isfile(
            "makedefaults"
        ), f"Makedefaults not found in {makedir}"
    return


def build_utility(
    modflow6_path,
    distribution_path,
    utility_name,
    target_name=None,
):
    # allow utility target name (zbud6) to be different from utility_name (zonebudget)
    if target_name is None:
        target_name = utility_name

    # setup the folder structure
    utility_path = os.path.join(distribution_path, "utils", utility_name)
    print(f"Creating {utility_name} files in {utility_path}")
    os.makedirs(utility_path)
    for sd in ["make", "msvs"]:
        d = os.path.join(utility_path, sd)
        os.makedirs(d)

    # copy the source folder to the distribution folder
    src = os.path.join(modflow6_path, "utils", utility_name, "src")
    dst = os.path.join(distribution_path, "utils", utility_name, "src")
    print(f"Copying {src} ===> {dst}")
    shutil.copytree(src, dst)

    # copy the visual studio project file
    src = os.path.join(
        modflow6_path, "utils", utility_name, "msvs", f"{utility_name}.vfproj"
    )
    dst = os.path.join(distribution_path, "utils", utility_name, "msvs")
    print(f"Copying {src} ===> {dst}")
    shutil.copy(src, dst)

    # if there are extra files then copy the extrafiles.txt
    extrafiles = None
    src = os.path.join(
        modflow6_path, "utils", utility_name, "pymake", "extrafiles.txt"
    )
    if os.path.isfile(src):
        dst = os.path.join(distribution_path, "utils", utility_name, "make")
        print(f"Copying {src} ===> {dst}")
        shutil.copy(src, dst)
        extrafiles = "extrafiles.txt"

    # use pymake to build a makefile
    build_makefile(utility_path, target=target_name, extrafiles=extrafiles)

    return


def download_published_reports(distribution_path):
    print("Downloading published reports.")
    for url in [
        "https://pubs.usgs.gov/tm/06/a57/tm6a57.pdf",
        "https://pubs.usgs.gov/tm/06/a55/tm6a55.pdf",
        "https://pubs.usgs.gov/tm/06/a56/tm6a56.pdf",
        "https://pubs.usgs.gov/tm/06/a61/tm6a61.pdf",
        "https://pubs.usgs.gov/tm/06/a62/tm6a62.pdf",
    ]:
        print("  downloading {}".format(url))
        destination = os.path.join(distribution_path, "doc")
        pymake.download_and_unzip(
            url, pth=destination, delete_zip=False, verify=False
        )
    print("\n")
    return


def clean_latex_files(modflow6_path):
    print("Cleaning latex files")
    check = False
    exts = ["pdf", "aux", "bbl", "idx", "lof", "out", "toc"]
    pth = os.path.join(modflow6_path, "doc", "mf6io")
    files = ["mf6io.{}".format(e) for e in exts]
    delete_files(files, pth, allow_failure=True)
    if check:
        assert not os.path.isfile(pth + ".pdf")

    pth = os.path.join(modflow6_path, "doc", "ReleaseNotes")
    files = ["ReleaseNotes.{}".format(e) for e in exts]
    delete_files(files, pth, allow_failure=True)
    if check:
        assert not os.path.isfile(pth + ".pdf")

    pth = os.path.join(modflow6_path, "doc", "zonebudget")
    files = ["zonebudget.{}".format(e) for e in exts]
    delete_files(files, pth, allow_failure=True)
    if check:
        assert not os.path.isfile(pth + ".pdf")

    pth = os.path.join(modflow6_path, "doc", "ConverterGuide")
    files = ["converter_mf5to6.{}".format(e) for e in exts]
    delete_files(files, pth, allow_failure=True)
    if check:
        assert not os.path.isfile(pth + ".pdf")

    pth = os.path.join(
        modflow6_path, "..", "modflow6-docs.git", "mf6suptechinfo"
    )
    files = ["mf6suptechinfo.{}".format(e) for e in exts]
    delete_files(files, pth, allow_failure=True)
    if check:
        assert not os.path.isfile(pth + ".pdf")

    pth = os.path.join(modflow6_path, "..", "modflow6-examples.git", "doc")
    files = ["mf6examples.{}".format(e) for e in exts]
    delete_files(files, pth, allow_failure=True)
    if check:
        assert not os.path.isfile(pth + ".pdf")

    return


def rebuild_tex_from_dfn(modflow6_path):
    print("Rebuilding the tex files from dfn by running mf6ivar.py")
    npth = os.path.join(modflow6_path, "doc", "mf6io", "mf6ivar")
    pth = "./"

    with cwd(npth):
        # get list of TeX files
        files = [
            f
            for f in os.listdir("tex")
            if os.path.isfile(os.path.join("tex", f))
        ]
        for f in files:
            fpth = os.path.join("tex", f)
            os.remove(fpth)

        # run python
        argv = ["python", "mf6ivar.py"]
        buff, ierr = run_command(
            argv, pth, verbose=True, terminate_on_failure=True
        )

        # get list for dfn files
        dfnfiles = [
            os.path.splitext(f)[0]
            for f in os.listdir("dfn")
            if os.path.isfile(os.path.join("dfn", f))
            and "dfn" in os.path.splitext(f)[1]
        ]
        texfiles = [
            os.path.splitext(f)[0]
            for f in os.listdir("tex")
            if os.path.isfile(os.path.join("tex", f))
            and "tex" in os.path.splitext(f)[1]
        ]
        missing = ""
        icnt = 0
        for f in dfnfiles:
            if "common" in f:
                continue
            fpth = "{}-desc".format(f)
            if fpth not in texfiles:
                icnt += 1
                missing += "  {:3d} {}.tex\n".format(icnt, fpth)
        msg = "\n{} TeX file(s) are missing. ".format(
            icnt
        ) + "Missing files:\n{}".format(missing)
        assert icnt == 0, msg

    return


def create_simple_testmodel(temp_path, bin_path):
    # build simple model
    print(f"Creating a simple test model in {temp_path}.")
    name = "mymodel"
    exe_name = "mf6"
    if sys.platform.lower() == "win32":
        exe_name += ".exe"
    exe_name = os.path.join(bin_path, exe_name)
    sim = flopy.mf6.MFSimulation(
        sim_name=name, sim_ws=temp_path, exe_name=exe_name
    )
    tdis = flopy.mf6.ModflowTdis(sim)
    ims = flopy.mf6.ModflowIms(sim)
    gwf = flopy.mf6.ModflowGwf(sim, modelname=name, save_flows=True)
    dis = flopy.mf6.ModflowGwfdis(gwf, nrow=10, ncol=10)
    ic = flopy.mf6.ModflowGwfic(gwf)
    npf = flopy.mf6.ModflowGwfnpf(gwf, save_specific_discharge=True)
    chd = flopy.mf6.ModflowGwfchd(
        gwf, stress_period_data=[[(0, 0, 0), 1.0], [(0, 9, 9), 0.0]]
    )
    oc = flopy.mf6.ModflowGwfoc(gwf, printrecord=[("BUDGET", "ALL")])
    sim.write_simulation()

    # return
    return


def update_mf6io_tex_files(
    modflow6_path,
    mf6bin_path,
    expth,
):
    texpth = os.path.join(modflow6_path, "doc", "mf6io")
    fname1 = os.path.join(texpth, "mf6output.tex")
    fname2 = os.path.join(texpth, "mf6noname.tex")
    fname3 = os.path.join(texpth, "mf6switches.tex")
    expth = os.path.abspath(expth)

    assert os.path.isfile(mf6bin_path), f"{mf6bin_path} does not exist"
    assert os.path.isdir(expth), f"{expth} does not exist"

    # run an example model
    abs_mf6bin_path = os.path.abspath(mf6bin_path)
    print(f"Running simple test model with {abs_mf6bin_path}.")
    cmd = [abs_mf6bin_path]
    simpth = expth
    buff, ierr = run_command(
        cmd, simpth, verbose=False, terminate_on_failure=True
    )
    lines = buff.split("\r\n")
    with open(fname1, "w") as f:
        f.write("{}\n".format("{\\small"))
        f.write("{}\n".format("\\begin{lstlisting}[style=modeloutput]"))
        for line in lines:
            f.write(line.rstrip() + "\n")
        f.write("{}\n".format("\\end{lstlisting}"))
        f.write("{}\n".format("}"))

    # run model without a namefile present
    print(f"Running mf6 without namefile present.")
    if os.path.isdir("./temp"):
        shutil.rmtree("./temp")
    os.mkdir("./temp")
    cmd = [abs_mf6bin_path]
    buff, ierr = run_command(
        cmd, "./temp", verbose=False, terminate_on_failure=False
    )
    lines = buff.split("\r\n")
    with open(fname2, "w") as f:
        f.write("{}\n".format("{\\small"))
        f.write("{}\n".format("\\begin{lstlisting}[style=modeloutput]"))
        for line in lines:
            f.write(line.rstrip() + "\n")
        f.write("{}\n".format("\\end{lstlisting}"))
        f.write("{}\n".format("}"))

    # run mf6 command with -h to show help
    print(f"Running mf6 with -h option to give help commands.")
    cmd = [abs_mf6bin_path, "-h"]
    buff, ierr = run_command(
        cmd, "./temp", verbose=False, terminate_on_failure=True
    )
    lines = buff.split("\r\n")
    with open(fname3, "w") as f:
        f.write("{}\n".format("{\\small"))
        f.write("{}\n".format("\\begin{lstlisting}[style=modeloutput]"))
        for line in lines:
            f.write(line.rstrip() + "\n")
        f.write("{}\n".format("\\end{lstlisting}"))
        f.write("{}\n".format("}"))

    return


def update_latex_releaseinfo(
    modflow6_path,
    distribution_path,
):
    pth = os.path.join(modflow6_path, "doc", "ReleaseNotes")
    files = ["folder_struct.tex"]
    delete_files(files, pth, allow_failure=True)

    abs_dp = os.path.abspath(distribution_path)
    cmd = ["python", "mk_folder_struct.py", "-dp", abs_dp]
    buff, ierr = run_command(cmd, pth, verbose=True, terminate_on_failure=True)

    # cmd = ["python", "mk_runtimecomp.py"]
    # buff, ierr = run_command(cmd, pth)
    # msg = "\nERROR {}: could not run {} on {}".format(ierr, cmd[0], cmd[1])
    # assert ierr == 0, buff + msg

    for f in files:
        assert os.path.isfile(os.path.join(pth, f)), (
            "File does not exist: " + f
        )

    return


def build_latex_docs(
    modflow6_path,
    modflow6_examples_path,
    distribution_path,
):
    print("Building latex files")
    modflow6_doc_path = os.path.join(modflow6_path, "doc")
    doclist = [
        (modflow6_doc_path, "mf6io", "mf6io"),
        (modflow6_doc_path, "ReleaseNotes", "ReleaseNotes"),
        (modflow6_doc_path, "zonebudget", "zonebudget"),
        (modflow6_doc_path, "ConverterGuide", "converter_mf5to6"),
        (modflow6_doc_path, "SuppTechInfo", "mf6suptechinfo"),
        (modflow6_examples_path, "doc", "mf6examples"),
    ]

    for p, d, t in doclist:
        print("Building latex document: {}".format(t))
        dirname = os.path.join(p, d)
        with cwd(dirname):
            pdflatexcmd = [
                "pdflatex",
                "-interaction=nonstopmode",
                "-halt-on-error",
                f"{t}.tex",
            ]

            print("  Pass 1/4...")
            cmd = pdflatexcmd
            buff, ierr = run_command(
                cmd, "./", verbose=True, terminate_on_failure=True
            )

            cmd = ["bibtex", os.path.splitext(t)[0] + ".aux"]
            print("  Pass 2/4...")
            buff, ierr = run_command(
                cmd, "./", verbose=True, terminate_on_failure=False
            )
            msg = "\nERROR {}: could not run {} on {}".format(
                ierr, cmd[0], cmd[1]
            )
            if ierr != 0:
                # This can happen with zonebudget, for example, which does not have any references.
                print(
                    f"Warning building {dirname}. "
                    + "Bibtex did not terminate normally. This may be normal."
                )
                print(buff + msg)

            print("  Pass 3/4...")
            cmd = pdflatexcmd
            buff, ierr = run_command(
                cmd, "./", verbose=True, terminate_on_failure=True
            )

            print("  Pass 4/4...")
            cmd = pdflatexcmd
            buff, ierr = run_command(
                cmd, "./", verbose=True, terminate_on_failure=True
            )

            fname = f"{t}.pdf"
            assert os.path.isfile(fname), "Could not find " + fname

    # copy fname into distribution
    dst = os.path.join(distribution_path, "doc")
    for p, d, t in doclist:
        src = os.path.join(p, d, t) + ".pdf"
        print(f"Copying latex document: {t} ===> {dst}")
        shutil.copy(src, dst)

    return


def latex_is_available():
    if shutil.which("pdflatex") is None:
        return False
    else:
        return True


def build_latex(
    modflow6_path,
    modflow6_examples_path,
    distribution_path,
):
    if latex_is_available():
        # set paths
        temp_path = "./temp"
        ext = ""
        if get_platform() == "windows":
            ext = ".exe"
        mf6bin_path = os.path.join(distribution_path, "bin", f"mf6{ext}")

        # build files needed for latex docs
        clean_latex_files(modflow6_path)
        rebuild_tex_from_dfn(modflow6_path)
        create_simple_testmodel(temp_path, mf6bin_path)
        update_mf6io_tex_files(modflow6_path, mf6bin_path, temp_path)
        update_latex_releaseinfo(modflow6_path, distribution_path)

        # build the pdfs from the latex docs
        build_latex_docs(
            modflow6_path, modflow6_examples_path, distribution_path
        )

        # clean up
        # if os.path.isdir(temp_path):
        #     shutil.rmtree(temp_path)

    else:
        print(
            "Warning. Latex is not available "
            + "so latex documents were not built."
        )
    return


def build_examples(modflow6_examples_path, distribution_path):
    print("Building examples")

    examples_destination = os.path.join(distribution_path, "examples")
    assert os.path.isdir(modflow6_examples_path)
    assert os.path.isdir(examples_destination)

    # next create all examples, but don't run them
    scripts_folder = os.path.join(modflow6_examples_path, "scripts")
    scripts_folder = os.path.abspath(scripts_folder)
    exclude_list = ["ex-gwf-capture.py"]
    scripts = [
        fname
        for fname in os.listdir(scripts_folder)
        if fname.endswith(".py")
        and fname.startswith("ex-")
        and fname not in exclude_list
    ]
    for script in scripts:
        dest = os.path.abspath(examples_destination)
        argv = [
            "python",
            script,
            "--no_run",
            "--no_plot",
            "--no_gif",
            "--destination",
            dest,
        ]  # no run no plot
        buff, ierr = run_command(
            argv, scripts_folder, verbose=True, terminate_on_failure=True
        )

    return


def get_list_simulation_folders(pth):
    # create list of directories in pth that contain mfsim.nam
    simulation_folders = []
    for root, dirs, files in os.walk(pth):
        for d in dirs:
            dwpath = os.path.join(root, d)
            if "mfsim.nam" in os.listdir(dwpath):
                simulation_folders.append(dwpath)
    simulation_folders = sorted(simulation_folders)
    return simulation_folders


def build_example_run_scripts_win(distribution_path):
    if "windows" != get_platform():
        return

    print("Building example run scripts")

    # assign path and assign mf6path relative to examples folder
    examples_destination = os.path.join(distribution_path, "examples")
    mf6path = os.path.join(distribution_path, "bin", "mf6.exe")

    # create list of folders with mfsim.nam
    simulation_folders = get_list_simulation_folders(examples_destination)

    # go through each simulation folder and add a run.bat file
    for dwpath in simulation_folders:
        fname = os.path.join(dwpath, "run.bat")
        print("Adding {}".format(fname))
        with open(fname, "w") as f:
            f.write("@echo off" + "\n")
            runbatloc = os.path.relpath(mf6path, start=dwpath)
            f.write(runbatloc + "\n")
            f.write("echo." + "\n")
            f.write("echo Run complete.  Press any key to continue" + "\n")
            f.write("pause>nul" + "\n")

    # add runall.bat, which runs all examples
    fname = os.path.join(examples_destination, "runall.bat")
    with open(fname, "w") as f:
        for dwpath in simulation_folders:
            d = os.path.relpath(dwpath, start=examples_destination)
            s = "cd {}".format(d)
            f.write(s + "\n")
            runbatloc = os.path.relpath(mf6path, start=dwpath)
            f.write(runbatloc + "\n")
            d = os.path.relpath(examples_destination, start=dwpath)
            s = "cd {}".format(d)
            f.write(s + "\n")
            s = ""
            f.write(s + "\n")
        f.write("pause" + "\n")

    return


def build_example_run_scripts_linux(distribution_path):
    if get_platform() == "windows":
        return

    print("Building example run scripts")

    # assign path and assign mf6path relative to examples folder
    examples_destination = os.path.join(distribution_path, "examples")
    mf6path = os.path.join(distribution_path, "bin", "mf6")

    # create list of folders with mfsim.nam
    simulation_folders = get_list_simulation_folders(examples_destination)

    # go through each simulation folder and add a run.bat file
    for dwpath in simulation_folders:
        fname = os.path.join(dwpath, "run.sh")
        print("Adding {}".format(fname))
        with open(fname, "w") as f:
            f.write("#!/bin/bash" + "\n")
            runloc = os.path.relpath(mf6path, start=dwpath)
            f.write(runloc + "\n")
            f.write("echo ." + "\n")
            # todo f.write("echo Run complete.  Press any key to continue" + "\n")
            # todo f.write("pause>nul" + "\n")
        # chmod +x
        st = os.stat(fname)
        os.chmod(fname, st.st_mode | stat.S_IEXEC)

    # add runall.sh, which runs all examples
    fname = os.path.join(examples_destination, "runall.sh")
    with open(fname, "w") as f:
        f.write("#!/bin/bash" + "\n")
        for dwpath in simulation_folders:
            d = os.path.relpath(dwpath, start=examples_destination)
            s = "cd {}".format(d)
            f.write(s + "\n")
            runloc = os.path.relpath(mf6path, start=dwpath)
            f.write(runloc + "\n")
            d = os.path.relpath(examples_destination, start=dwpath)
            s = "cd {}".format(d)
            f.write(s + "\n")
            s = ""
            f.write(s + "\n")
        # todo f.write("pause" + "\n")
    # chmod +x
    st = os.stat(fname)
    os.chmod(fname, st.st_mode | stat.S_IEXEC)

    return


def build_and_run_examples(
    modflow6_examples_path,
    distribution_path,
    keep,
):
    if latex_is_available():
        print(
            "Building and running examples so that mf6examples.pdf can be built with LaTex."
        )

        print("Running modflow6examples.")
        # run modflow6examples/etc/ci_build_files.py -r to build and run examples
        script_path = os.path.join(modflow6_examples_path, "scripts")
        scripts = [
            file_name
            for file_name in sorted(os.listdir(script_path))
            if file_name.endswith(".py") and file_name.startswith("ex-")
        ]
        for s in scripts:
            args = ["python", s, "--no_gif"]
            buff, ierr = run_command(
                args, pth=script_path, verbose=True, terminate_on_failure=True
            )
            if not keep:
                examples_pth = os.path.join(modflow6_examples_path, "examples")
                clean_dirs = [
                    dir_name
                    for dir_name in os.listdir(examples_pth)
                    if s.replace(".py", "") in dir_name
                ]
                for dir_name in clean_dirs:
                    clean_example_dir(os.path.join(examples_pth, dir_name))

        # run process-scripts.py in modflow6examples/scripts.  Once completed, the build_latex()
        # script can make mf6examples.pdf
        print("Running the process-scripts.py command.")
        buff, ierr = run_command(
            ["python", "process-scripts.py"],
            script_path,
            verbose=True,
            terminate_on_failure=True,
        )
    else:
        print(
            "Skipping building and running of examples because latex is not available."
        )
    return


def clean_example_dir(dir_pth):
    print(f"deleting...'{dir_pth}'")
    shutil.rmtree(dir_pth)


def copy_meson_files(modflow6_path, distribution_path):
    meson_files = paths_for_filename("meson.build", modflow6_path)
    for meson_file in meson_files:
        src = os.path.join(modflow6_path, meson_file)
        dst = os.path.join(distribution_path, meson_file)
        if not os.path.exists(dst):
            print(f"Copying {src} ===> {dst}")
            shutil.copy(src, dst)
    return


def zipdir(dirname, zipname):
    print("Zipping directory: {}".format(dirname))
    zipf = zipfile.ZipFile(zipname, "w", zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(dirname):
        for file in files:
            if ".DS_Store" not in file:
                fname = os.path.join(root, file)
                print("  Adding to zip: ==> ", fname)
                zipf.write(fname, arcname=fname)
    zipf.close()
    print("\n")
    return


if __name__ == "__main__":
    # command line usages
    # python make_distribution.py [options]
    #   options include:
    #     -dp <distribution path>
    #     -mf6p <mf6 repository path>
    #     -mf6ep <mf6 examples repo path>
    #     -fc <fortran compiler>
    #   examples:
    #     python make_distribution.py -dp ./mf6.3.0 -mf6p ../modflow6-fork.git -mf6ep ../modflow6-examples.git --isApproved
    #     python make_distribution.py -dp ./mf6.3.0_linux -mf6p ../modflow6-fork.git -mf6ep ../modflow6-examples.git -fc ifort
    #     python make_distribution.py -dp ./distribution/mf6dev -mf6p ../modflow6-fork.git -mf6ep ../modflow6-examples.git
    #     python -c "import make_distribution; make_distribution.build_example_run_scripts_linux('./distribution/mf6dev')"

    # set paths
    modflow6_path = get_modflow6_path()
    modflow6_examples_path = get_modflow6_examples_path()
    distribution_path = get_distribution_path()

    # set fortran compiler
    fortran_compiler = get_compiler()

    # set keep
    keep = get_keep()

    do_step = True

    if do_step:
        set_modflow6_release_info(modflow6_path)

    if do_step:
        initialize_new_distribution(modflow6_path, distribution_path)

    if do_step:
        copy_visual_studio_files(modflow6_path, distribution_path)

    if do_step:
        build_makefile(distribution_path)

    if do_step:
        meson_build_binaries(modflow6_path)
        copy_binaries(modflow6_path, distribution_path)

    if do_step:
        build_utility(modflow6_path, distribution_path, "zonebudget", "zbud6")
        build_utility(modflow6_path, distribution_path, "mf5to6")

    if do_step:
        copy_meson_files(modflow6_path, distribution_path)

    if do_step:
        build_examples(modflow6_examples_path, distribution_path)
        build_example_run_scripts_win(distribution_path)
        build_example_run_scripts_linux(distribution_path)

    if do_step:
        build_and_run_examples(
            modflow6_examples_path,
            distribution_path,
            keep,
        )

    if do_step:
        # todo: mk_runtimecomp.py
        build_latex(modflow6_path, modflow6_examples_path, distribution_path)

    if do_step:
        download_published_reports(distribution_path)

    if do_step:
        zipname = distribution_path
        zipname += ".zip"
        zipdir(distribution_path, zipname)
        assert os.path.exists(zipname), f"Could not find zipfile: {zipname}"

    print(f"Done creating distribution: {zipname}")
