"""
Wrapper around all env XML for a case.

All interaction with and between the module files in XML/ takes place
through the Case module.
"""

from CIME.XML.standard_module_setup import *
from CIME.utils import expect, run_cmd
from CIME.XML.machines import Machines

from CIME.XML.env_test          import EnvTest
from CIME.XML.env_mach_specific import EnvMachSpecific
from CIME.XML.env_case          import EnvCase
from CIME.XML.env_mach_pes      import EnvMachPes
from CIME.XML.env_build         import EnvBuild
from CIME.XML.env_run           import EnvRun
from CIME.XML.env_archive       import EnvArchive
from CIME.XML.env_batch         import EnvBatch

logger = logging.getLogger(__name__)

class Case(object):

    def __init__(self, case_root=os.getcwd()):
        
        # Init first, if no valid case_root expect fails and tears down object, __del__ expects self._env_files_that_need_rewrite
        self._env_files_that_need_rewrite = set()
        
        expect(os.path.isdir(case_root),
               "Case root directory '%s' does not exist" % case_root)

        logger.debug("Initializing Case.")       
        self._env_entryid_files = []
        self._env_generic_files = []

        self._env_files_that_need_rewrite = set()
      

        self._env_entryid_files.append(EnvRun(case_root))
        self._env_entryid_files.append(EnvBuild(case_root))
        self._env_entryid_files.append(EnvMachPes(case_root))
        self._env_entryid_files.append(EnvCase(case_root))
        self._env_entryid_files.append(EnvBatch(case_root))
        if os.path.isfile(os.path.join(case_root,"env_test.xml")):
            self._env_entryid_files.append(EnvTest(case_root))
        self._env_generic_files.append(EnvMachSpecific(case_root))
        self._env_generic_files.append(EnvArchive(case_root))

        self._case_root = case_root
  
       

    def __del__(self):
        self.flush()

    def flush(self):
        for env_file in self._env_files_that_need_rewrite:
            env_file.write()

        self._env_files_that_need_rewrite = set()

    def get_value(self, item, attribute={}, resolved=True, subgroup=None):
        result = None
        for env_file in self._env_entryid_files:
            # Wait and resolve in self rather than in env_file
           
            result = env_file.get_value(item, attribute, resolved=False, subgroup=subgroup)
          
            if result is not None:
                if resolved and type(result) is str:
                    return self.get_resolved_value(result)
                return result
                
        for env_file in self._env_generic_files:
      
            result = env_file.get_value(item, attribute, resolved=False, subgroup=subgroup)
    
            if result is not None:
                if resolved and type(result) is str:
                    return self.get_resolved_value(result)
                return result
       
        # Return empty result
        return result


    def get_values(self, item=None, attribute={}, resolved=True, subgroup=None):
        
        """
        Return info object for given item, return all info for all item if item is empty.     
        """
  
        results = []
        for env_file in self._env_entryid_files:
            # Wait and resolve in self rather than in env_file
            result = None
           
            try:
                # env_batch has its own implementation of get_values otherwise in entry_id
                result = env_file.get_values(item, attribute, resolved=False, subgroup=subgroup)
                # Method exists, and was used.  
            except AttributeError:
                # Method does not exist.  What now?
                logger.debug("No get_values method for class %s (%s)" , env_file.__class__.__name__ , AttributeError)
               

            if result is not None and (len(result) >= 1):
                if resolved and type(result) is str:
                    # WRONG
                    logger.info("Fix this line , it is an array not a string")
                    results.append(self.get_resolved_value(result))
                else :
                    results = results + result
                return results
            
        for env_file in self._env_generic_files:

            result = env_file.get_values(item, attribute, resolved=False, subgroup=subgroup)
      
            if result is not None and (len(result) >=1) :
                if resolved and type(result) is str:
                    logger.debug("Type string and resolved is true")
                    results.append(self.get_resolved_value(result))
                else :
                    logger.debug("Append result to return list (%s)" ,result)
                    results = results + result
                return results
   
        logger.warning("Not able to retrieve any value")
        # Return empty result
        return results
        


    def get_type_info(self, item):
        result = None
        for env_file in self._env_entryid_files:
            result = env_file.get_type_info(item)
            if result is not None:
                return result

        logging.info("Not able to retreive type for item '%s'" % item)

    def get_resolved_value(self, item, recurse=0):
        num_unresolved = item.count("$")
        recurse_limit = 10
        if (num_unresolved > 0 and recurse < recurse_limit ):
            for env_file in self._env_entryid_files:
                result = env_file.get_resolved_value(item)
                item = result
            if ("$" not in item):
                return item
            else:
                self.get_resolved_value(item,recurse=recurse+1)

        if(recurse >= recurse_limit):
            logging.warning("Not able to fully resolve item '%s'" % item)

        return item

    def set_value(self, item, value, subgroup=None, ignore_type=False):
        for env_file in self._env_entryid_files:
            result = env_file.set_value(item, value, subgroup, ignore_type)
            if (result is not None):
                self._env_files_that_need_rewrite.add(env_file)
                return result

        logging.warning("Not able to set value for item '%s'" % item)


    def __iter__(self):
        for entryid_file in self._env_entryid_files:
            for key, val in entryid_file:
                if type(val) is str and '$' in val:
                    yield key, self.get_resolved_value(val)
                else:
                    yield key, val


